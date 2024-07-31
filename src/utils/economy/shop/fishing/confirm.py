import hikari
import miru
from miru.abc.item import InteractiveViewItem

from bot import get_setting
from utils.fishing.bait import Bait


class FishingConfirmView(miru.View):
    def __init__(self, user: hikari.User, bait: Bait, amount: int) -> None:
        super().__init__(timeout=None)
        self.bait = bait
        self.amount = amount
        self.embed = hikari.Embed(
            title='Purchase Confirmation',
            description= f'Are you sure you want to purchase **{bait.emoji} {bait.name} ({amount}x)**?\n ',
            color=get_setting('general', 'embed_color')
        )
        self.add_item(miru.Button(
            custom_id='confirm',
            label='Confirm',
            style=hikari.ButtonStyle.PRIMARY
        ))
        self.add_item(miru.Button(
            custom_id='cancel',
            label='Cancel',
            style=hikari.ButtonStyle.DANGER
        ))
        self.author = user
        self.response = None
    
    async def _handle_callback(self, item: InteractiveViewItem, ctx: miru.ViewContext) -> None:
        if item.custom_id == 'confirm':
            self.response = 'confirm'
        elif item.custom_id == 'cancel':
            self.response = 'cancel'
            self.embed = hikari.Embed(
                title='Purchase Cancelled',
                description='You have cancelled the purchase of the bait.',
                color=get_setting('general', 'embed_error_color')
            )
        await ctx.edit_response(embed=self.embed, components=[])
        self.stop()
    
    async def view_check(self, ctx: miru.ViewContext) -> bool:
        return ctx.user.id == self.author.id