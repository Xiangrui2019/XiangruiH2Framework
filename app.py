from xiangruih2framework.app import App

app = App()

async def index(request, response):
    await response.send_view("index", app="我的HTTP2App")

async def post(request, response):
    await response.send_view("post", a=request.getformparameter("a"), n=request.getformparameter("n"))

app.get("/api/{id}", index)
app.post("/post", post)

app.start()