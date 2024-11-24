import axios from "axios";

export function useLoader() {

    const API = "http://localhost:8000/colladata/api/v1";

    function url(path) {
        if (!path.startsWith('/')) {
            return API + '/' + path;
        }
        return API + path
    }

    function get(path, params=null, headers=null) {
        const options = { withCredentials: true };
        if (params) { options.params = params }
        if (headers) { options.headers = headers }
        return axios.get(url(path), options)
            .then(response => response.data)
    }

    function post(path, body, params=null, headers=null) {
        const options = { withCredentials: true };
        if (params) { options.params = params }
        if (headers) { options.headers = headers }
        return axios.post(url(path), body, options)
            .then(response => response.data)
    }

    function postImage(path, file, params=null, headers=null) {
        const options = {
            withCredentials: true,
            headers: headers ? headers : {}
        };
        options.headers = { "Content-Type": "multipart/form-data" }
        if (params) { options.params = params }

        const formData = new FormData();
        formData.append("file", file);
        return axios.postForm(url(path), formData, options)
            .then(response => response.data)
    }

    return { get, post, postImage }
}