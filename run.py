from app import app, db, login_manager
from werkzeug.security import generate_password_hash
import logging


# Set up user loader after all imports
@login_manager.user_loader
def load_user(user_id):
    from models import User
    return User.query.get(int(user_id))



# Import routes to register them with the app
import routes

def init_database():
    """Initialize database with admin user and sample data"""
    # Import models after app context is available
    from models import User, Category, Product

    with app.app_context():
        # Create all tables
        db.create_all()

        # Create admin user if not exists
        admin_user = User.query.filter_by(username='admin').first()
        if not admin_user:
            admin_user = User(
                username='admin',
                email='admin@luxuryproducts.ge',
                password_hash=generate_password_hash('admin123'),
                is_admin=True
            )
            db.session.add(admin_user)
            db.session.commit()
            logging.info("Admin user created: admin/admin123")

        # Create sample data
        create_sample_data()


def create_sample_data():
    """Create sample categories and products"""
    from models import Category, Product

    if Category.query.count() == 0:
        # Create categories
        categories = [
            Category(name='საათები', description='ლუქს საათები'),
            Category(name='სამკაულები', description='ძვირფასი სამკაულები'),
            Category(name='ჩანთები', description='დიზაინერული ჩანთები'),
            Category(name='პარფიუმერია', description='ელიტარული პარფიუმერია'),
            Category(name='კოსმეტიკა', description='პრემიუმ კოსმეტიკა')
        ]

        for category in categories:
            db.session.add(category)
        db.session.commit()

        # Create sample products
        products = [
            Product(name='Rolex Submariner', description='ლუქს საათი ყველაზე კარგი ხარისხით',
                    price=25000, category_id=1, featured=True,
                    image_url='https://swisswatches-magazine.com/uploads/2024/09/rolex-submariner-titlepicture.webp'),
            Product(name='Cartier Love Bracelet', description='ლეგენდარული სამკაული',
                    price=8500, category_id=2, featured=True,
                    image_url='data:image/jpeg;base64,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'),
            Product(name='Hermès Birkin', description='ყველაზე ექსკლუზიური ჩანთა',
                    price=15000, category_id=3, featured=True,
                    image_url='https://i.ebayimg.com/images/g/A0QAAOSwiLdlo9hW/s-l1600.webp'),
            Product(name='Chanel No. 5', description='ღია და ელეგანტური არომატი',
                    price=150, category_id=4, featured=True,
                    image_url='https://aromati.ge/wp-content/uploads/2025/01/Chanel-No-5-eau-de-parfum.jpg'),
            Product(name='La Mer Moisturizer', description='ლუქს კოსმეტიკა',
                    price=350, category_id=5, featured=True,
                    image_url='https://www.cremedelamer.com/media/export/cms/products/responsive/lm_sku_332002_4x5_0.png?width=900&height=1125'),
            Product(name='Patek Philippe', description='შვეიცარული საათი',
                    price=45000, category_id=1, featured=True,
                    image_url='https://nivadagrenchenofficial.com/cdn/shop/files/f77-stainless-steel-dark-blue-aventurine-787106_120x.jpg?v=1747223835')
        ]

        for product in products:
            db.session.add(product)
        db.session.commit()


# Initialize database when the module is imported
init_database()

if __name__ == '__main__':
    # Run the app
    app.run(host='0.0.0.0', port=5000, debug=True)