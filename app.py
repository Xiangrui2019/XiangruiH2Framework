from xiangruih2framework.app import App
from controllers.IndexController import IndexController

app = App()

app.get("/", IndexController.Home)
app.post("/add", IndexController.Add)

app.start()