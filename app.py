from xiangruih2framework.app import App

app = App()

async def index(request, response):
    response.set_header("content-type", "text/html; charset=UTF-8")
    await response.send(bytes("<button>{}</button>".format(request.getrouteparameter("id")), encoding='utf-8'))

async def post(request, response):
    response.set_header("content-type", "text/html; charset=UTF-8")
    print(request.getformparameter("a"))
    await response.send(bytes("老鼠", encoding="utf-8"))

app.get("/api/{id}", index)
app.post("/post", post)

app.start()