from app import *
from file_controller import *
from admin import *

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug = True)