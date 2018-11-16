try:
    import logger
    import helpers
    import pil
    import dlfuncs
except ImportError:
    from . import logger
    from . import helpers
    from . import pil
    from . import dlfuncs

    def start():
        if not helpers.check_lock_file():
            helpers.create_lock_user()
            dlfuncs.get_broadcasts_info()

            if pil.dl_lives:
                if pil.livestream_obj:
                    logger.info("Livestream available, starting download.")
                    dlfuncs.download_livestream()
                else:
                    logger.info('There are no available livestreams.')
            else:
                logger.binfo("Livestream saving is disabled either with an argument or in the config file.")

            logger.separator()

            if pil.dl_replays:
                if pil.replays_obj:
                    logger.info(
                        '{:d} {:s} available, beginning download.'.format(len(pil.replays_obj), "replays" if len(
                            pil.replays_obj) > 1 else "replay"))
                    dlfuncs.download_replays()
                else:
                    logger.info('There are no available replays.')
            else:
                logger.binfo("Replay saving is disabled either with an argument or in the config file.")

            helpers.remove_lock()
            logger.separator()

        else:
            logger.warn("Lock file is already present for this user, there is probably another download ongoing.")
            logger.warn("If this is not the case, manually delete the file '{:s}' and try again.".format(
                pil.dl_user + '.lock'))
            logger.separator()
