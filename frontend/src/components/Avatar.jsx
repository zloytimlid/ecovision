/** User avatar: the uploaded photo, or the first letter of the username. */
export default function Avatar({ user, size = 'h-16 w-16', textSize = 'text-2xl' }) {
  if (user?.avatar_url) {
    return <img src={user.avatar_url} alt="" className={`${size} shrink-0 rounded-full bg-gray-100 object-cover`} />
  }
  const letter = (user?.username || '?').charAt(0).toUpperCase()
  return (
    <span
      className={`${size} ${textSize} flex shrink-0 items-center justify-center rounded-full bg-emerald-600 font-bold text-white`}
      aria-hidden
    >
      {letter}
    </span>
  )
}
