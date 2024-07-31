import miru

from miru.ext import nav

from utils.profile.inventory import Inventory

class ChecksView(nav.NavigatorView):
    def __init__(self, inventory: Inventory, pages, buttons, timeout, autodefer: bool = True) -> None:
        super().__init__(pages=pages, items=buttons, timeout=timeout, autodefer=autodefer)
        self.inventory = inventory

    async def view_check(self, ctx: miru.ViewContext) -> bool:
        return ctx.user.id == self.inventory.user.id