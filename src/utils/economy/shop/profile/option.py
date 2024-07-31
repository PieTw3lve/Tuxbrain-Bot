import miru

class ProfileOptionSelect(miru.SelectOption):
    def __init__(self, item: tuple) -> None:
        super().__init__(label=item[0], description='Click To View', value=item[1])