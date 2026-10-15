import api from './client.js'

export async function register(username, password) {
  const { data } = await api.post('/auth/register/', { username, password })
  return data
}

export async function login(username, password) {
  const { data } = await api.post('/auth/login/', { username, password })
  return data
}

export async function logout() {
  await api.post('/auth/logout/')
}

export async function getMe() {
  const { data } = await api.get('/auth/me/')
  return data
}

/** Change username and/or e-mail. */
export async function updateMe(payload) {
  const { data } = await api.patch('/auth/me/', payload)
  return data
}

export async function uploadAvatar(imageBlob) {
  const form = new FormData()
  form.append('avatar', imageBlob, 'avatar.jpg')
  const { data } = await api.post('/auth/me/avatar/', form)
  return data
}

export async function deleteAvatar() {
  const { data } = await api.delete('/auth/me/avatar/')
  return data
}

/** Returns the new token: the server logs out all other sessions. */
export async function changePassword(currentPassword, newPassword) {
  const { data } = await api.post('/auth/me/password/', {
    current_password: currentPassword,
    new_password: newPassword,
  })
  return data.token
}

export async function deleteAccount(password) {
  await api.delete('/auth/me/', { data: { password } })
}
