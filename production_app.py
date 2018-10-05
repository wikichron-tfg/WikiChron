from wikichron.app import create_app, set_up_app, init_app

# create and config Dash instance
app = create_app()

# set layout, import startup js and bind callbacks
set_up_app(app)

# init auxiliar servers & deps
init_app(app)

wikichron = app.server
