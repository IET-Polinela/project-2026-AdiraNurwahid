const BASE_URL = "https://103.151.63.71:8006";

async function requestAPI(endpoint, method="GET", bodyData=null){

    const token = localStorage.getItem("access_token");

    const options = {
        method: method,
        headers: {
            "Content-Type": "application/json"
        }
    };

    if(token){
        options.headers["Authorization"] = `Bearer ${token}`;
    }

    if(bodyData){
        options.body = JSON.stringify(bodyData);
    }

    const response = await fetch(BASE_URL + endpoint, options);

    return response;
}