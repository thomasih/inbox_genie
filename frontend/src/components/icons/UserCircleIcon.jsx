import * as React from "react"

function UserCircleIcon(props) {
  return (
    <svg viewBox="0 0 24 24" fill="none" {...props}>
      <circle cx={12} cy={8} r={4} stroke="currentColor" strokeWidth={1.5} />
      <path stroke="currentColor" strokeWidth={1.5} d="M4 20c0-2.21 3.582-4 8-4s8 1.79 8 4" />
    </svg>
  )
}

export default UserCircleIcon
