// Utilities
import { defineStore } from 'pinia'

export const useTooltip = defineStore('tooltip', {
    state: () => ({
        data: null,
        x: 0,
        y: 0
    }),

    actions: {

        show(data, x, y) {
            this.x = x;
            this.y = y;
            this.data = data;
        },

        hide() {
            this.data = null;
        }
    }
})
