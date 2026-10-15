export default function ImagePreview({ src, alt = 'Фото предмета', children }) {
  return (
    <div className="relative overflow-hidden rounded-2xl bg-gray-100">
      <img src={src} alt={alt} className="block h-auto w-full" />
      {children}
    </div>
  )
}
