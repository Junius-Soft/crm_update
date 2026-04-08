import { h } from 'vue'
import FeatherIcon from 'frappe-ui'

export function TemplateOption({ active, option, variant, icon, onClick }) {
  return h(
    'button',
    {
      class: [
        active ? 'bg-surface-gray-2' : 'text-ink-gray-7',
        'group flex w-full gap-2 items-center rounded-md px-2 py-2 text-base hover:bg-surface-gray-3',
        variant == 'danger' ? 'text-ink-red-3 hover:bg-ink-red-1' : '',
      ],
      onClick: onClick,
    },
    [
      icon
        ? h(FeatherIcon, {
            name: icon,
            class: ['h-4 w-4 shrink-0'],
            'aria-hidden': true,
          })
        : null,
      h('span', { class: 'whitespace-nowrap' }, option),
    ],
  )
}

/**
 * @param {Ref<boolean>} isConfirmingDelete - Ref to track confirmation state
 * @param {Function} onConfirmDelete - Callback when delete is confirmed
 * @param {string} label - Label for the delete option
 * @returns {Array} Array of option objects for use in dropdowns
 */
export function ConfirmDelete({
  isConfirmingDelete,
  onConfirmDelete,
  label = __('Delete'),
}) {
  return [
    {
      label,
      component: (props) =>
        TemplateOption({
          option: label,
          icon: 'trash-2',
          active: props.active,
          variant: 'grey',
          onClick: (event) => {
            event.preventDefault()
            event.stopImmediatePropagation()
            isConfirmingDelete.value = true
          },
        }),
      condition: () => !isConfirmingDelete.value,
    },
    {
      label: __('Confirm {0}', [label]),
      component: (props) =>
        TemplateOption({
          option: __('Confirm {0}', [label]),
          icon: 'trash-2',
          active: props.active,
          variant: 'danger',
          onClick: () => {
            onConfirmDelete()
            // Reset state after confirming
            isConfirmingDelete.value = false
          },
        }),
      condition: () => isConfirmingDelete.value,
    },
  ]
}