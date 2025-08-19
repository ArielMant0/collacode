<template>
    <div class="d-flex align-center justify-center">
        <v-checkbox
            :model-value="warningsEnabled"
            label="enable warnings"
            color="primary"
            @update:model-value="setWarnings"
            hide-details
            hide-spin-buttons
            density="compact"/>

        <v-checkbox
            :model-value="crowdFilter"
            :label="'show only crowd '+app.itemName+'s'"
            color="primary"
            class="ml-4"
            @update:model-value="value => app.setCrowdFilter(value)"
            hide-details
            hide-spin-buttons
            density="compact"/>
    </div>
</template>

<script setup>
    import { useApp } from '@/store/app';
    import { useTimes } from '@/store/times';
    import { setUserWarnings } from '@/use/data-api';
import DM from '@/use/data-manager';
import { getTagWarnings, getWarningSize } from '@/use/similarities';
    import { storeToRefs } from 'pinia';
    import { onMounted, watch } from 'vue';
    import { useToast } from 'vue-toastification';

    const app = useApp()
    const times = useTimes()
    const toast = useToast()

    const { warningsEnabled, crowdFilter } = storeToRefs(app)

    async function setWarnings(value) {
        try {
            await setUserWarnings(value)
            times.needsReload("users")
        } catch (e) {
            console.error(e.toString())
            toast.error("error updating warning setting")
        }
    }

    function setCrowdFilter() {
        app.setCrowdFilter(crowdFilter.value)
    }

    onMounted(setCrowdFilter)

    watch(() => times.similarity, setCrowdFilter)
    watch(crowdFilter, function() {
        const data = DM.getData("items", false)
        data.forEach(g => {
            const sims = DM.getDataItem("similarity_item", g.id)
            if (sims) {
                g.warnings = getTagWarnings(g, sims, data)
                g.numWarnings = getWarningSize(g, null, false)
                g.numWarningsAll = getWarningSize(g, null, true)
            } else {
                g.warnings = []
                g.numWarnings = 0
                g.numWarningsAll = 0
            }
        })
    })

</script>
