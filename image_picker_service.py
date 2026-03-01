"""Servico Python para camera/galeria via image_picker Flutter."""
from dataclasses import dataclass
from typing import Optional
from flet.controls.base_control import control
from flet.controls.services.service import Service


@dataclass
class ImagePickerResult:
    name: str
    path: str
    base64: str


@control("flet_image_picker")
class ImagePickerService(Service):

    async def pick_image_camera(
        self,
        image_quality: int = 85,
        max_width: Optional[float] = None,
        max_height: Optional[float] = None,
    ) -> Optional[ImagePickerResult]:
        result = await self._invoke_method(
            "pick_image_camera",
            {
                "image_quality": image_quality,
                "max_width": max_width,
                "max_height": max_height,
            },
            timeout=3600,
        )
        if result:
            return ImagePickerResult(
                name=result["name"],
                path=result["path"],
                base64=result["base64"],
            )
        return None

    async def pick_image_gallery(
        self,
        image_quality: int = 85,
        max_width: Optional[float] = None,
        max_height: Optional[float] = None,
    ) -> Optional[ImagePickerResult]:
        result = await self._invoke_method(
            "pick_image_gallery",
            {
                "image_quality": image_quality,
                "max_width": max_width,
                "max_height": max_height,
            },
            timeout=3600,
        )
        if result:
            return ImagePickerResult(
                name=result["name"],
                path=result["path"],
                base64=result["base64"],
            )
        return None
