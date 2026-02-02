"""
Tests de Integración - Operaciones de Base de Datos

Prueba operaciones CRUD y queries en MongoDB y PostgreSQL.
"""

import pytest
from datetime import datetime, timedelta
import uuid

from app.infrastructure.database import (
    get_mongodb_client,
    get_postgresql_client,
    AlgorithmRepository,
    AnalysisRepository,
    UserRepository,
)
from app.infrastructure.database.models.mongo import (
    Algorithm,
    AnalysisResult,
    PatternDetection,
)
from app.infrastructure.database.models.postgres import User
from app.core.security import hash_password

@pytest.mark.integration
class TestMongoDBOperations:
    """Tests de operaciones en MongoDB"""
    
    @pytest.mark.asyncio
    async def test_mongodb_connection(self):
        """Test conexión a MongoDB"""
        client = get_mongodb_client()
        # Si no está conectado, conectar
        if client.client is None:
            await client.connect()
        
        is_connected = await client.ping()
        assert is_connected is True
        
        # NO cerrar el cliente singleton - se cerrará al final de la sesión
    
    @pytest.mark.asyncio
    async def test_algorithm_repository_create(self):
        """Test creación de algoritmo"""
        repo = AlgorithmRepository()
        
        algorithm = Algorithm(
            name=f"test_algorithm_{uuid.uuid4().hex[:8]}",
            code="algorithm test(n)\nbegin\n    x ← 1\nend",
            language="pseudocode",
            category="testing",
            tags=["test", "integration"],
            description="Algoritmo de prueba para integración",
        )
        
        created = await repo.create(algorithm)
        
        assert created.id is not None
        assert created.name == algorithm.name
        assert created.category == "testing"
        
        # Limpiar
        await repo.delete(str(created.id))
    
    @pytest.mark.asyncio
    async def test_algorithm_repository_get_by_id(self):
        """Test obtener algoritmo por ID"""
        repo = AlgorithmRepository()
        
        # Crear algoritmo
        algorithm = Algorithm(
            name=f"test_get_{uuid.uuid4().hex[:8]}",
            code="algorithm test(n)\nbegin\n    x ← 1\nend",
            language="pseudocode",
        )
        created = await repo.create(algorithm)
        
        # Obtener por ID
        retrieved = await repo.get_by_id(str(created.id))
        
        assert retrieved is not None
        assert retrieved.id == created.id
        assert retrieved.name == created.name
        
        # Limpiar
        await repo.delete(str(created.id))
    
    @pytest.mark.asyncio
    async def test_algorithm_repository_update(self):
        """Test actualizar algoritmo"""
        repo = AlgorithmRepository()
        
        # Crear
        algorithm = Algorithm(
            name=f"test_update_{uuid.uuid4().hex[:8]}",
            code="algorithm test(n)\nbegin\n    x ← 1\nend",
            language="pseudocode",
        )
        created = await repo.create(algorithm)
        
        # Actualizar
        updated = await repo.update(
            str(created.id),
            {"description": "Descripción actualizada", "category": "updated"}
        )
        
        assert updated is not None
        assert updated.description == "Descripción actualizada"
        assert updated.category == "updated"
        
        # Limpiar
        await repo.delete(str(created.id))
    
    @pytest.mark.asyncio
    async def test_algorithm_repository_delete(self):
        """Test eliminar algoritmo"""
        repo = AlgorithmRepository()
        
        # Crear
        algorithm = Algorithm(
            name=f"test_delete_{uuid.uuid4().hex[:8]}",
            code="algorithm test(n)\nbegin\n    x ← 1\nend",
            language="pseudocode",
        )
        created = await repo.create(algorithm)
        algo_id = str(created.id)
        
        # Eliminar
        deleted = await repo.delete(algo_id)
        assert deleted is True
        
        # Verificar que no existe
        retrieved = await repo.get_by_id(algo_id)
        assert retrieved is None
    
    @pytest.mark.asyncio
    async def test_algorithm_repository_list(self):
        """Test listar algoritmos"""
        repo = AlgorithmRepository()
        
        # Crear varios algoritmos
        algorithms = []
        for i in range(3):
            algo = Algorithm(
                name=f"test_list_{i}_{uuid.uuid4().hex[:8]}",
                code=f"algorithm test{i}(n)\nbegin\n    x ← {i}\nend",
                language="pseudocode",
            )
            created = await repo.create(algo)
            algorithms.append(created)
        
        # Listar
        listed = await repo.list(skip=0, limit=100)
        
        assert len(listed) >= 3
        
        # Limpiar
        for algo in algorithms:
            await repo.delete(str(algo.id))
    
    @pytest.mark.asyncio
    async def test_algorithm_repository_search_by_category(self):
        """Test buscar por categoría"""
        repo = AlgorithmRepository()
        
        # Crear algoritmos con categoría específica
        test_category = f"test_category_{uuid.uuid4().hex[:8]}"
        algorithms = []
        
        for i in range(2):
            algo = Algorithm(
                name=f"test_cat_{i}_{uuid.uuid4().hex[:8]}",
                code=f"algorithm test{i}(n)\nbegin\n    x ← {i}\nend",
                language="pseudocode",
                category=test_category,
            )
            created = await repo.create(algo)
            algorithms.append(created)
        
        # Buscar por categoría
        found = await repo.search_by_category(test_category)
        
        assert len(found) >= 2
        for algo in found:
            if algo.id in [a.id for a in algorithms]:
                assert algo.category == test_category
        
        # Limpiar
        for algo in algorithms:
            await repo.delete(str(algo.id))
    
    @pytest.mark.asyncio
    async def test_algorithm_repository_search_by_tags(self):
        """Test buscar por tags"""
        repo = AlgorithmRepository()
        
        # Crear algoritmos con tags específicos
        test_tag = f"test_tag_{uuid.uuid4().hex[:8]}"
        algorithms = []
        
        for i in range(2):
            algo = Algorithm(
                name=f"test_tag_{i}_{uuid.uuid4().hex[:8]}",
                code=f"algorithm test{i}(n)\nbegin\n    x ← {i}\nend",
                language="pseudocode",
                tags=[test_tag, "integration"],
            )
            created = await repo.create(algo)
            algorithms.append(created)
        
        # Buscar por tag
        found = await repo.search_by_tags([test_tag])
        
        assert len(found) >= 2
        for algo in found:
            if algo.id in [a.id for a in algorithms]:
                assert test_tag in algo.tags
        
        # Limpiar
        for algo in algorithms:
            await repo.delete(str(algo.id))
    
    @pytest.mark.asyncio
    async def test_analysis_repository_create(self):
        """Test creación de resultado de análisis"""
        algo_repo = AlgorithmRepository()
        analysis_repo = AnalysisRepository()
        
        # Crear algoritmo primero
        algorithm = Algorithm(
            name=f"test_analysis_{uuid.uuid4().hex[:8]}",
            code="algorithm test(n)\nbegin\n    for i ← 1 to n do\n        x ← x + 1\nend",
            language="pseudocode",
        )
        created_algo = await algo_repo.create(algorithm)
        
        # Crear análisis
        analysis = AnalysisResult(
            algorithm=created_algo,
            big_o="O(n)",
            omega="Ω(n)",
            theta="Θ(n)",
            analysis_time=0.123,
        )
        
        created_analysis = await analysis_repo.create(analysis)
        
        assert created_analysis.id is not None
        assert created_analysis.big_o == "O(n)"
        # El algoritmo puede ser un Document o un Link - verificar el ID en ambos casos
        algo_id = created_analysis.algorithm.id if hasattr(created_analysis.algorithm, 'id') else created_analysis.algorithm.ref.id
        assert algo_id == created_algo.id
        
        # Limpiar
        await analysis_repo.delete(str(created_analysis.id))
        await algo_repo.delete(str(created_algo.id))
    
    @pytest.mark.asyncio
    async def test_analysis_repository_get_by_algorithm_id(self):
        """Test obtener análisis por ID de algoritmo"""
        algo_repo = AlgorithmRepository()
        analysis_repo = AnalysisRepository()
        
        # Crear algoritmo
        algorithm = Algorithm(
            name=f"test_get_analysis_{uuid.uuid4().hex[:8]}",
            code="algorithm test(n)\nbegin\n    x ← 1\nend",
            language="pseudocode",
        )
        created_algo = await algo_repo.create(algorithm)
        
        # Crear análisis
        analysis = AnalysisResult(
            algorithm=created_algo,
            big_o="O(1)",
            omega="Ω(1)",
            analysis_time=0.01,
        )
        created_analysis = await analysis_repo.create(analysis)
        
        # Obtener por algorithm_id
        found = await analysis_repo.get_by_algorithm_id(str(created_algo.id))
        
        assert len(found) >= 1
        assert any(a.id == created_analysis.id for a in found)
        
        # Limpiar
        await analysis_repo.delete(str(created_analysis.id))
        await algo_repo.delete(str(created_algo.id))
    
    @pytest.mark.asyncio
    async def test_analysis_repository_get_latest_by_algorithm(self):
        """Test obtener análisis más reciente de un algoritmo"""
        algo_repo = AlgorithmRepository()
        analysis_repo = AnalysisRepository()
        
        # Crear algoritmo
        algorithm = Algorithm(
            name=f"test_latest_{uuid.uuid4().hex[:8]}",
            code="algorithm test(n)\nbegin\n    x ← 1\nend",
            language="pseudocode",
        )
        created_algo = await algo_repo.create(algorithm)
        
        # Crear varios análisis
        analyses = []
        for i in range(3):
            analysis = AnalysisResult(
                algorithm=created_algo,
                big_o=f"O({i})",
                omega=f"Ω({i})",
                analysis_time=0.01 * i,
            )
            created = await analysis_repo.create(analysis)
            analyses.append(created)
        
        # Obtener el más reciente
        latest = await analysis_repo.get_latest_by_algorithm(str(created_algo.id))
        
        assert latest is not None
        assert latest.id == analyses[-1].id  # Debe ser el último creado
        
        # Limpiar
        for analysis in analyses:
            await analysis_repo.delete(str(analysis.id))
        await algo_repo.delete(str(created_algo.id))
    
    @pytest.mark.asyncio
    async def test_analysis_repository_search_by_complexity(self):
        """Test buscar análisis por complejidad"""
        algo_repo = AlgorithmRepository()
        analysis_repo = AnalysisRepository()
        
        # Crear algoritmo
        algorithm = Algorithm(
            name=f"test_complexity_search_{uuid.uuid4().hex[:8]}",
            code="algorithm test(n)\nbegin\n    x ← 1\nend",
            language="pseudocode",
        )
        created_algo = await algo_repo.create(algorithm)
        
        # Crear análisis con complejidad específica
        analysis = AnalysisResult(
            algorithm=created_algo,
            big_o="O(n²)",
            omega="Ω(n²)",
            theta="Θ(n²)",
            analysis_time=0.05,
        )
        created_analysis = await analysis_repo.create(analysis)
        
        # Buscar por complejidad
        found = await analysis_repo.search_by_complexity(big_o="O(n²)")
        
        assert len(found) >= 1
        assert any(a.id == created_analysis.id for a in found)
        
        # Limpiar
        await analysis_repo.delete(str(created_analysis.id))
        await algo_repo.delete(str(created_algo.id))

@pytest.mark.integration
class TestPostgreSQLOperations:
    """Tests de operaciones en PostgreSQL"""
    
    @pytest.mark.asyncio
    async def test_postgresql_connection(self):
        """Test conexión a PostgreSQL"""
        client = get_postgresql_client()
        await client.connect()
        
        assert client.engine is not None
        assert client.session_factory is not None
        
        await client.close()
    
    @pytest.mark.asyncio
    async def test_user_repository_create(self):
        """Test creación de usuario"""
        client = get_postgresql_client()
        await client.connect()
        
        async with client.get_session() as session:
            repo = UserRepository(session)
            
            # Crear usuario único
            email = f"test_{uuid.uuid4().hex[:8]}@example.com"
            username = f"testuser_{uuid.uuid4().hex[:8]}"
            
            user = await repo.create_user(
                email=email,
                username=username,
                password="test_password_123",
            )
            
            assert user.id is not None
            assert user.email == email
            assert user.username == username
            assert user.is_active is True
            
            # Limpiar
            await repo.delete(str(user.id))
        
        await client.close()
    
    @pytest.mark.asyncio
    async def test_user_repository_get_by_email(self):
        """Test obtener usuario por email"""
        client = get_postgresql_client()
        await client.connect()
        
        async with client.get_session() as session:
            repo = UserRepository(session)
            
            # Crear usuario
            email = f"test_{uuid.uuid4().hex[:8]}@example.com"
            user = await repo.create_user(
                email=email,
                username=f"testuser_{uuid.uuid4().hex[:8]}",
                password="test_password",
            )
            
            # Obtener por email
            found = await repo.get_by_email(email)
            
            assert found is not None
            assert found.id == user.id
            assert found.email == email
            
            # Limpiar
            await repo.delete(str(user.id))
        
        await client.close()
    
    @pytest.mark.asyncio
    async def test_user_repository_authenticate(self):
        """Test autenticación de usuario"""
        client = get_postgresql_client()
        await client.connect()
        
        async with client.get_session() as session:
            repo = UserRepository(session)
            
            # Crear usuario
            email = f"test_{uuid.uuid4().hex[:8]}@example.com"
            password = "secure_password_123"
            
            user = await repo.create_user(
                email=email,
                username=f"testuser_{uuid.uuid4().hex[:8]}",
                password=password,
            )
            
            # Autenticar correctamente
            authenticated = await repo.authenticate(email, password)
            assert authenticated is not None
            assert authenticated.id == user.id
            
            # Autenticar con password incorrecta
            not_authenticated = await repo.authenticate(email, "wrong_password")
            assert not_authenticated is None
            
            # Limpiar
            await repo.delete(str(user.id))
        
        await client.close()
    
    @pytest.mark.asyncio
    async def test_user_repository_update_password(self):
        """Test actualizar password de usuario"""
        client = get_postgresql_client()
        await client.connect()
        
        async with client.get_session() as session:
            repo = UserRepository(session)
            
            # Crear usuario
            email = f"test_{uuid.uuid4().hex[:8]}@example.com"
            old_password = "old_password_123"
            new_password = "new_password_456"
            
            user = await repo.create_user(
                email=email,
                username=f"testuser_{uuid.uuid4().hex[:8]}",
                password=old_password,
            )
            
            # Actualizar password
            updated = await repo.update_password(str(user.id), new_password)
            assert updated is True
            
            # Verificar que la nueva password funciona
            authenticated = await repo.authenticate(email, new_password)
            assert authenticated is not None
            
            # Verificar que la vieja password no funciona
            not_authenticated = await repo.authenticate(email, old_password)
            assert not_authenticated is None
            
            # Limpiar
            await repo.delete(str(user.id))
        
        await client.close()
    
    @pytest.mark.asyncio
    async def test_user_repository_deactivate_activate(self):
        """Test desactivar y activar usuario"""
        client = get_postgresql_client()
        await client.connect()
        
        async with client.get_session() as session:
            repo = UserRepository(session)
            
            # Crear usuario
            email = f"test_{uuid.uuid4().hex[:8]}@example.com"
            user = await repo.create_user(
                email=email,
                username=f"testuser_{uuid.uuid4().hex[:8]}",
                password="test_password",
            )
            
            assert user.is_active is True
            
            # Desactivar
            deactivated = await repo.deactivate_user(str(user.id))
            assert deactivated is True
            
            # Verificar que está desactivado
            user_check = await repo.get_by_id(str(user.id))
            assert user_check.is_active is False
            
            # Activar
            activated = await repo.activate_user(str(user.id))
            assert activated is True
            
            # Verificar que está activo
            user_check = await repo.get_by_id(str(user.id))
            assert user_check.is_active is True
            
            # Limpiar
            await repo.delete(str(user.id))
        
        await client.close()
    
    @pytest.mark.asyncio
    async def test_user_repository_search_users(self):
        """Test buscar usuarios"""
        client = get_postgresql_client()
        await client.connect()
        
        async with client.get_session() as session:
            repo = UserRepository(session)
            
            # Crear usuarios con prefijo específico
            search_prefix = f"search_{uuid.uuid4().hex[:6]}"
            users = []
            
            for i in range(2):
                user = await repo.create_user(
                    email=f"{search_prefix}_{i}@example.com",
                    username=f"{search_prefix}_user_{i}",
                    password="test_password",
                )
                users.append(user)
            
            # Buscar usuarios
            found = await repo.search_users(search_prefix, limit=10)
            
            assert len(found) >= 2
            
            # Limpiar
            for user in users:
                await repo.delete(str(user.id))
        
        await client.close()
    
    @pytest.mark.asyncio
    async def test_user_repository_count_users(self):
        """Test contar usuarios"""
        client = get_postgresql_client()
        await client.connect()
        
        async with client.get_session() as session:
            repo = UserRepository(session)
            
            # Contar todos los usuarios
            total_count = await repo.count_users()
            assert total_count >= 0
            
            # Contar solo usuarios activos
            active_count = await repo.count_users(active_only=True)
            assert active_count >= 0
            assert active_count <= total_count
        
        await client.close()

@pytest.mark.integration
class TestDatabaseFactory:
    """Tests del Database Factory"""
    
    @pytest.mark.asyncio
    async def test_database_factory_create_mongodb(self):
        """Test factory para MongoDB"""
        from app.infrastructure.database import DatabaseFactory, DatabaseBackend
        
        client = await DatabaseFactory.create_client(DatabaseBackend.MONGODB)
        
        assert client is not None
        
        await client.close()
    
    @pytest.mark.asyncio
    async def test_database_factory_create_postgresql(self):
        """Test factory para PostgreSQL"""
        from app.infrastructure.database import DatabaseFactory, DatabaseBackend
        
        client = await DatabaseFactory.create_client(DatabaseBackend.POSTGRESQL)
        
        assert client is not None
        
        await client.close()
    
    def test_repository_factory_create_algorithm_repository(self):
        """Test factory para AlgorithmRepository"""
        from app.infrastructure.database import RepositoryFactory, DatabaseBackend
        
        factory = RepositoryFactory(DatabaseBackend.MONGODB)
        repo = factory.create_algorithm_repository()
        
        assert isinstance(repo, AlgorithmRepository)
    
    def test_repository_factory_create_analysis_repository(self):
        """Test factory para AnalysisRepository"""
        from app.infrastructure.database import RepositoryFactory, DatabaseBackend
        
        factory = RepositoryFactory(DatabaseBackend.MONGODB)
        repo = factory.create_analysis_repository()
        
        assert isinstance(repo, AnalysisRepository)