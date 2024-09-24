const urlParams = new URLSearchParams(window.location.search);
const code = urlParams.get('code')
const state = urlParams.get('state')
// TODO(developer): Set to client ID and API key from the Developer Console
// const CLIENT_ID = '1072241143702-td5u5l5e00trg8s0duls6vo7odvpchca.apps.googleusercontent.com';
// const API_KEY = 'AIzaSyB9bBA_4leiCH7a3w0S87FTJ6euFoSC9z0';

// // Discovery doc URL for APIs used by the quickstart
// const DISCOVERY_DOC = 'https://www.googleapis.com/discovery/v1/apis/calendar/v3/rest';

// // Authorization scopes required by the API; multiple scopes can be
// // included, separated by spaces.
// const SCOPES = 'https://www.googleapis.com/auth/calendar';
// let tokenClient;
// let gapiInited = false;
// let gisInited = false;

if (code && state) {
  axios.post('https://api.line.me/oauth2/v2.1/token', {
    grant_type: 'authorization_code',
    code: code,
    redirect_uri: 'https://de80-184-22-228-220.ngrok-free.app/static',
    client_id: '2006369648',
    client_secret: '5981702a6ab21c422062666f0feb9df2'
  }, {
    headers: {
      'Content-Type': 'application/x-www-form-urlencoded'
    }
  }).then(result => {
    axios.post('https://de80-184-22-228-220.ngrok-free.app/google/auth', {
      token: String(result.data.access_token)
    }).then(ans => {
      console.log('ans', ans)
      window.localStorage.setItem('_x', ans.data?.userId)
    })
  }).catch(err => {
    window.localStorage.removeItem('_x')
    window.location.href = `https://access.line.me/oauth2/v2.1/authorize?response_type=code&client_id=2006369648&redirect_uri=https://de80-184-22-228-220.ngrok-free.app/static&state=${new Date().getTime()}&scope=profile`
  })
} else {
  window.localStorage.removeItem('_x')
  window.location.href = `https://access.line.me/oauth2/v2.1/authorize?response_type=code&client_id=2006369648&redirect_uri=https://de80-184-22-228-220.ngrok-free.app/static&state=${new Date().getTime()}&scope=profile`
}

//google
function loginWithGoogle() {
  document.getElementById('google_file').click()
}

document.getElementById('google_file').addEventListener('change', (event) => {
  const google_btn = document.getElementById('google_btn')
  google_btn.disabled = true
  const form = event.target
  const formData = new FormData()
  formData.append('file', form.files[0])
  formData.append('user', window.localStorage.getItem('_x'))
  fetch('/google/upload', {
    method: 'POST',
    body: formData,
  }).then(response => {
    if (response.ok) {
      // Clear the file input after successful submission
      event.target.value = ''
      google_btn.disabled = false
    }
  }).catch(error => {
    console.error('File upload failed:', error)
    google_btn.disabled = false
  })
})

function syncWithGoogle() {
  axios.post('/google/start', {
    user: window.localStorage.getItem('_x')
  }).then(result => {
    console.log('result =', result)
  }).catch(err => {
    console.log('err', err)
  })
}

//microsoft
function loginWithMicrosoft() {
  window.location.href = "https://login.microsoftonline.com/"
}