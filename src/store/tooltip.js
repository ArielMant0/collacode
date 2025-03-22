// Utilities
import DM from '@/use/data-manager';
import { useMouse } from '@vueuse/core';
import { defineStore } from 'pinia'

let delayT = null;

export const useTooltip = defineStore('tooltip', {
    state: () => ({
        data: null,
        x: 0,
        y: 0,
        align: "right",

        evidence: null,
        evidenceData: null,
        eX: 0,
        eY: 0,
    }),

    actions: {

        show(data, x, y, align="right") {
            this.x = x;
            this.y = y;
            this.align = align
            this.data = data;
        },

        showAfterDelay(data, x, y, delay=350, align="right") {
            const mouse = useMouse()
            if (delayT !== null) {
                clearTimeout(delayT)
                delayT = null
            }
            delayT = setTimeout(() => {
                delayT = null;
                if (mouse.x.value === x && mouse.y.value === y) {
                    this.x = x;
                    this.y = y;
                    this.align = align
                    this.data = data;
                }
            }, delay)
        },

        hide() {
            this.data = null;
        },

        showEvidence(id, x, y) {
            this.eX = x;
            this.eY = y;
            this.evidenceData = id ? DM.getDataItem("evidence", id) : null
            this.evidence = id;
        },

        hideEvidence() {
            this.evidence = null;
            this.evidenceData = null;
        }
    }
})
