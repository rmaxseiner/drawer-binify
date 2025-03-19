from app.database import Base, get_db, engine
from app.models import User, Drawer, Bin, Baseplate, Model
from app.services.baseplate_generator_service import BaseplateService
from pathlib import Path
import asyncio

async def test_baseplate_reuse():
    # Create database tables
    Base.metadata.create_all(bind=engine)
    print('Database tables created')
    
    # Get database session
    db = next(get_db())
    
    # Create baseplate generation service
    baseplate_service = BaseplateService(db, Path('generated_files'))
    
    # Generate a baseplate with specific dimensions
    baseplate1, files1 = await baseplate_service.generate_baseplate('TestBaseplate1', 252.0, 252.0)
    print(f'First baseplate generated: id={baseplate1.id}, model_id={baseplate1.model_id}')
    print(f'Files generated: {len(files1)}')
    
    # Generate another baseplate with the same dimensions
    baseplate2, files2 = await baseplate_service.generate_baseplate('TestBaseplate2', 252.0, 252.0)
    print(f'Second baseplate generated: id={baseplate2.id}, model_id={baseplate2.model_id}')
    print(f'Files generated: {len(files2)}')
    
    # Check if the model IDs match (indicating reuse)
    if baseplate1.model_id == baseplate2.model_id:
        print('Model reuse SUCCESSFUL: Both baseplates are using the same model')
    else:
        print('Model reuse FAILED: Baseplates are using different models')
    
    # Generate a baseplate with different dimensions
    baseplate3, files3 = await baseplate_service.generate_baseplate('TestBaseplate3', 336.0, 210.0)
    print(f'Third baseplate generated (different dimensions): id={baseplate3.id}, model_id={baseplate3.model_id}')
    print(f'Files generated: {len(files3)}')
    
    # Check that this baseplate has a different model ID
    if baseplate1.model_id != baseplate3.model_id:
        print('Dimension check PASSED: Different dimensions resulted in different models')
    else:
        print('Dimension check FAILED: Different dimensions resulted in the same model')
    
    # Query all models
    models = db.query(Model).filter(Model.type == "baseplate").all()
    print(f'Total baseplate models in database: {len(models)}')
    for i, model in enumerate(models):
        print(f'Model {i+1}: id={model.id}, type={model.type}, metadata={model.model_metadata}')

# Run the test
if __name__ == "__main__":
    asyncio.run(test_baseplate_reuse())