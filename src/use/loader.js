import axios from "axios";

export function useLoader() {

    const API = "http://localhost:8000/api/v1";

    function url(path) {
        if (!path.startsWith('/')) {
            return API + '/' + path;
        }
        return API + path
    }

    function get(path, params) {
        const options = params ? { params: params } : {};
        return axios.get(url(path), options)
            .then(response => response.data)
    }

    function post(path, body, params) {
        const options = params ? { params: params } : {};
        return axios.post(url(path), body, options)
            .then(response => response.data)
    }

    function postImage(path, file, params) {
        const options = params ? { params: params } : {};
        options.headers = { "Content-Type": "multipart/form-data" }
        const formData = new FormData();
        formData.append("file", file);
        return axios.postForm(url(path), formData, options)
            .then(response => response.data)
    }

    return { get, post, postImage }
}