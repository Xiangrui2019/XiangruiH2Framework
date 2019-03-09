class IndexController():
    
    @staticmethod
    async def Home(request, response):
        await response.send_view("index", appname="我的HTTP2 App")

    @staticmethod
    async def Add(request, response):
        await response.send_view("add", data=request.getformparameter("data"))