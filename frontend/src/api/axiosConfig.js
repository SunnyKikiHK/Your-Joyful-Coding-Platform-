import axios from 'axios';

const api = axios.create({
    baseURL: 'http://127.0.0.1:8000',
});

//request interceptor to automatically attach the jwt token
api.interceptors.request.use(
    (config) => {
        //grab the token from local storage
        const token = localStorage.getItem('token');
        
        if (token) {
            config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
    },
    (error) => {
        return Promise.reject(error);
    }
);

export default api;