export const APP_ANONYMOUS = "false"
export const APP_BASE_PATH = "/collacode"
export const APP_START_PAGE = "coding"
export const URL_TEASER = "media/teaser/"
export const URL_EVIDENCE = "media/evidence/"
export const URL_STATIC_DATA = "data/"
export const URL_SOUND = "https://www2.visus.uni-stuttgart.de/collacode/sounds/"
export const URL_IMAGES = "https://www2.visus.uni-stuttgart.de/collacode/images/"
export const ALLOWED_HOSTS = false
export const VERSION = "v0.1.0"

export function getApiUrl() {
    return `https://www2.visus.uni-stuttgart.de/colladata/api/v1`
}

export function getPort(port=3000) {
    return port && !Number.isNaN(port) ? port : 3000
}