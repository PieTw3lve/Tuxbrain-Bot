import hikari
import miru

from miru.ext import nav

class NavPageInfo(nav.NavButton):
    def __init__(self, pages: int, row: int):
        super().__init__(label="Page: 1", style=hikari.ButtonStyle.SECONDARY, disabled=True, row=row)
        self.pages = pages

    async def callback(self, ctx: miru.ViewContext) -> None:
        return

    async def before_page_change(self) -> None:
        self.label = f'Page: {self.view.current_page+1}/{self.pages}'