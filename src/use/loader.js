import axios from "axios";

export function useLoader() {

    function url(path) {
        if (!path.startsWith('/')) {
            return __API_URL__ + '/' + path;
        }
        return __API_URL__ + path
    }

    async function get(path, params=null, headers=null) {
        if (__APP_STATIC__) return
        const options = { withCredentials: true };
        if (params) { options.params = params }
        if (headers) { options.headers = headers }
        const response = await axios.get(url(path), options);
        return response.data;
    }

    async function post(path, body, params=null, headers=null) {
        if (__APP_STATIC__) return
        const options = { withCredentials: true };
        if (params) { options.params = params }
        if (headers) { options.headers = headers }
        const response = await axios.post(url(path), body, options);
        return response.data;
    }

    async function postImage(path, file, params=null, headers=null) {
        if (__APP_STATIC__) return
        const options = {
            withCredentials: true,
            headers: headers ? headers : {}
        };
        options.headers = { "Content-Type": "multipart/form-data" }
        if (params) { options.params = params }

        const formData = new FormData();
        formData.append("file", file);
        const response = await axios.postForm(url(path), formData, options);
        return response.data;
    }

    return { get, post, postImage }
}