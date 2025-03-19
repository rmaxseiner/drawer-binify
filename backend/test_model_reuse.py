from app.database import Base, get_db, engine
from app.models import User, Drawer, Bin, Baseplate, Model
from app.services.bin_generation_service import BinGenerationService
from pathlib import Path
import asyncio

async def test_bin_reuse():
    # Create database tables
    Base.metadata.create_all(bind=engine)
    print('Database tables created')
    
    # Get database session
    db = next(get_db())
    
    # Create bin generation service
    bin_service = BinGenerationService(db, Path('generated_files'))
    
    # Generate a bin with specific dimensions
    bin1, files1 = await bin_service.generate_bin('TestBin1', 42.0, 42.0, 25.0)
    print(f'First bin generated: id={bin1.id}, model_id={bin1.model_id}')
    print(f'Files generated: {len(files1)}')
    
    # Generate another bin with the same dimensions
    bin2, files2 = await bin_service.generate_bin('TestBin2', 42.0, 42.0, 25.0)
    print(f'Second bin generated: id={bin2.id}, model_id={bin2.model_id}')
    print(f'Files generated: {len(files2)}')
    
    # Check if the model IDs match (indicating reuse)
    if bin1.model_id == bin2.model_id:
        print('Model reuse SUCCESSFUL: Both bins are using the same model')
    else:
        print('Model reuse FAILED: Bins are using different models')
    
    # Generate a bin with different dimensions
    bin3, files3 = await bin_service.generate_bin('TestBin3', 84.0, 42.0, 25.0)
    print(f'Third bin generated (different dimensions): id={bin3.id}, model_id={bin3.model_id}')
    print(f'Files generated: {len(files3)}')
    
    # Check that this bin has a different model ID
    if bin1.model_id != bin3.model_id:
        print('Dimension check PASSED: Different dimensions resulted in different models')
    else:
        print('Dimension check FAILED: Different dimensions resulted in the same model')
    
    # Query all models
    models = db.query(Model).all()
    print(f'Total models in database: {len(models)}')
    for i, model in enumerate(models):
        print(f'Model {i+1}: id={model.id}, type={model.type}, metadata={model.model_metadata}')

# Run the test
if __name__ == "__main__":
    asyncio.run(test_bin_reuse())