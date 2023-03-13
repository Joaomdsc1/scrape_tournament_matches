from typing import Annotated, NewType

Id = Annotated[NewType("Id", str), "{current-name}@/{sport}/{country}/{name}-{year}"]
NoSeasonId = Annotated[NewType("NoSeasonId", str), "{current-name}@/{sport}/{country}"]
