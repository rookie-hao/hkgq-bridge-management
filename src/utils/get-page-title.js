import defaultSettings from '@/settings'

const title = defaultSettings.title || '港澳台侨管库系统'

export default function getPageTitle(pageTitle) {
  if (pageTitle) {
    return `${pageTitle} - ${title}`
  }
  return `${title}`
}
