import { createContext, useContext, useEffect, useLayoutEffect, useState } from 'react'

const PHONE_UA = /iPhone|iPod|Windows Phone|IEMobile|Opera Mini|BlackBerry|Android.+Mobile|Mobile/i
const TABLET_UA = /iPad|Tablet|PlayBook|Silk|Android(?!.+Mobile)/i

/** "phone" | "tablet" | "desktop", from the user agent. */
export function detectDevice() {
  const ua = navigator.userAgent
  // iPadOS 13+ reports itself as a Mac; a Mac with a touch screen is an iPad.
  const iPadAsMac = /Macintosh/.test(ua) && navigator.maxTouchPoints > 1
  if (TABLET_UA.test(ua) || iPadAsMac) return 'tablet'
  if (navigator.userAgentData?.mobile || PHONE_UA.test(ua)) return 'phone'
  return 'desktop'
}

/**
 * Layout for the current device: phones always get the mobile layout, computers the
 * desktop one. Tablets and narrow desktop windows are decided by the viewport width.
 */
export function detectLayout(device = detectDevice()) {
  if (device === 'phone') return 'mobile'
  const minWidth = device === 'tablet' ? 1024 : 768
  return window.matchMedia(`(min-width: ${minWidth}px)`).matches ? 'desktop' : 'mobile'
}

const DeviceContext = createContext({ device: 'desktop', layout: 'mobile', isDesktop: false })

export function DeviceProvider({ children }) {
  const [device] = useState(detectDevice)
  const [layout, setLayout] = useState(() => detectLayout(device))

  useEffect(() => {
    const update = () => setLayout(detectLayout(device))
    window.addEventListener('resize', update)
    window.addEventListener('orientationchange', update)
    return () => {
      window.removeEventListener('resize', update)
      window.removeEventListener('orientationchange', update)
    }
  }, [device])

  // Drives the `desktop:` Tailwind variant (see index.css).
  useLayoutEffect(() => {
    document.documentElement.dataset.layout = layout
    document.documentElement.dataset.device = device
  }, [layout, device])

  return (
    <DeviceContext.Provider value={{ device, layout, isDesktop: layout === 'desktop' }}>
      {children}
    </DeviceContext.Provider>
  )
}

export default function useDevice() {
  return useContext(DeviceContext)
}
