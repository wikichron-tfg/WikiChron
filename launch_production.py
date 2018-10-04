from gunicorn.app.base import Application
from wikichron.app import create_app, set_up_app, init_app

class WikiChronGunicorn(Application):

    def __init__(self):
        # create and config Dash instance
        app = create_app()

        # set layout, import startup js and bind callbacks
        set_up_app(app)

        # init auxiliar servers & deps
        init_app(app)

        self.application = app.server
        super().__init__()


    def load(self):
        return self.application


    def load_config(self):
        self.options = super().load_config_from_file('gunicorn_config.py')

if __name__ == "__main__":
    WikiChronGunicorn().run()
