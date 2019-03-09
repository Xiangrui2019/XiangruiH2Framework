from xiangruih2framework.app import App

app = App()

async def index(request, response):
    response.set_header("content-type", "text/html; charset=UTF-8")
    await response.send(bytes("<button>{}</button>".format(request.getrouteparameter("id")), encoding='utf-8'))

app.get("/{id}", index)

app.start()