from xiangruih2framework.app import App

app = App()

async def index(request, response):
    print(str(request.geturlparams("id")))
    await response.send(bytes("<button>{}</button>".format("dsf"), encoding='utf-8'))

app.get("/{id}", index)

app.start()