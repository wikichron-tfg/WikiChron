from app import create_app, set_up_app, init_app, run

# create and config Dash instance
app = create_app()

#~ # set layout, import startup js and bind callbacks
set_up_app(app)

#~ # init auxiliar servers & deps
init_app(app)


run(app)
