// Utilities
import DM from '@/use/data-manager';
import { defineStore } from 'pinia'

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
