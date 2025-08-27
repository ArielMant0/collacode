<template>
    <v-text-field v-model="datetime"
        type="datetime-local"
        :min="min"
        :max="max"
        :style="{ minWidth: minW, maxWidth: maxW }"
        density="compact"
        hide-details
        hide-spin-buttons
        @update:model-value="onUpdate"
        >
    </v-text-field>
</template>

<script setup>
    import { DateTime } from 'luxon'
    import { computed } from 'vue'

    const model = defineModel({ type: [Date, null], required: true })
    const props = defineProps({
        min: { type: Date },
        max: { type: Date },
        max: { type: Date },
        minWidth: { type: [Number, String], default: "auto" },
        maxWidth: { type: [Number, String], default: "auto" }
    })

    const minW = computed(() => typeof props.minWidth === "string" ?
        props.minWidth : props.minWidth+'px')
    const maxW = computed(() => typeof props.maxWidth === "string" ?
        props.maxWidth : props.maxWidth+'px')

    const datetime = ref(model.value ?
        DateTime.fromJSDate(model.value).toFormat("yyyy-MM-dd hh:mm") :
        ""
    )

    function onUpdate() {
        const str = datetime.value.replace("T", " ")
        model.value = DateTime.fromFormat(str, "yyyy-MM-dd hh:mm").toJSDate()
    }

</script>