# path: f2/apps/weibo/dl.py

from typing import Any, Dict, List, Union

from f2.log.logger import logger
from f2.i18n.translator import _
from f2.dl.base_downloader import BaseDownloader
from f2.apps.weibo.utils import format_file_name
from f2.apps.weibo.api import WeiboAPIEndpoints


class WeiboDownloader(BaseDownloader):
    def __init__(self, kwargs: dict = ...) -> None:
        if kwargs["cookie"] is None:
            raise ValueError(
                _(
                    "cookie不能为空。请提供有效的 cookie 参数，或自动从浏览器获取 `--auto-cookie edge`"
                )
            )

        super().__init__(kwargs)

    async def create_download_tasks(
        self,
        kwargs: Dict,
        weibo_datas: Union[List, Dict],
        user_path: Any = ...,
    ) -> None:
        """
        创建下载任务

        Args:
            kwargs (dict): 命令行参数
            weibo_datas (list, dict): 微博数据列表或字典
            user_path (str): 用户目录路径
        """

        if (
            not kwargs
            or not weibo_datas
            or not isinstance(weibo_datas, (list, dict))
            or not user_path
        ):
            return

        # 统一处理，将 weibo_datas 转为列表
        weibo_datas_list = (
            [weibo_datas] if isinstance(weibo_datas, dict) else weibo_datas
        )

        # 创建下载任务
        for weibo_data in weibo_datas_list:
            await self.handler_download(kwargs, weibo_data, user_path)

        # 执行下载任务
        await self.execute_tasks()

    async def handler_download(
        self, kwargs: Dict, weibo_data_dict: Dict, user_path: Any
    ) -> None:
        """
        处理下载任务

        Args:
            kwargs (Dict): 命令行参数
            weibo_data_dict (Dict): 作品数据字典
            user_path (Any): 用户目录路径
        """

        # 构建文件夹路径
        self.base_path = (
            user_path
            / format_file_name(kwargs.get("naming", "{create}_{desc}"), weibo_data_dict)
            if kwargs.get("folderize")
            else user_path
        )
        self.user_id = weibo_data_dict.get("user_id")
        self.weibo_id = weibo_data_dict.get("weibo_id")
        self.kwargs = kwargs
        self.weibo_data_dict = weibo_data_dict

        # mblogtype: 2    # 0 微博 1 热门微博 2 置顶微博

        # 检查微博是否可见
        if self.weibo_data_dict.get("weibo_is_visible"):
            logger.error(_("微博：{0} 无查看权限").format(self.weibo_id))
            return

        else:
            logger.debug(_("开始下载微博：{0}").format(self.weibo_id))
            await self.download_desc()

        # 检查微博是否有图片
        if (
            self.weibo_data_dict.get("weibo_pic_num") == 0
            and weibo_data_dict.get("is_video") == "11"
        ):
            await self.download_video()
        else:
            await self.download_images()

        return

    async def download_video(self):
        logger.debug(
            _("清晰度列表：{0}，码率列表：{1}").format(
                self.weibo_data_dict.get("quality_list"),
                self.weibo_data_dict.get("bitrate_list"),
            )
        )

        video_name = (
            format_file_name(
                self.kwargs.get("naming", "{create}_{desc}"), self.weibo_data_dict
            )
            + "_video"
        )
        video_url = self.weibo_data_dict.get("playback_list")

        if video_url:
            await self.initiate_download(
                _("视频"),
                video_url,
                self.base_path,
                video_name,
                ".mp4",
            )

    async def download_desc(self):
        # 处理文案下载任务
        desc_name = (
            format_file_name(
                self.kwargs.get("naming", "{create}_{desc}"), self.weibo_data_dict
            )
            + "_desc"
        )
        desc_content = self.weibo_data_dict.get("weibo_desc_raw")
        await self.initiate_static_download(
            _("文案"), desc_content, self.base_path, desc_name, ".txt"
        )

    async def download_images(self):
        for i, image_url in enumerate(self.weibo_data_dict.get("weibo_pic_ids", [])):
            image_name = f"{format_file_name(self.kwargs.get('naming'), self.weibo_data_dict)}_image_{i + 1}"
            image_url = WeiboAPIEndpoints.LARGEST + f"/{image_url}"
            if image_url != None:
                await self.initiate_download(
                    _("图片"), image_url, self.base_path, image_name, ".jpg"
                )
            else:
                logger.warning(
                    _("{0} 该微博没有图片链接，无法下载").format(self.weibo_id)
                )
