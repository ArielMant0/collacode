<template>
    <v-sheet class="pa-0">
        <div v-if="!loading" style="width: 100%;" class="pa-2">
            <div class="mt-4 mb-8" style="overflow-x: auto;">
                <ExtDimsBars/>
            </div>

        </div>
    </v-sheet>
</template>

<script setup>
    import ExtDimsBars from '../externalization/ExtDimsBars.vue';

    const props = defineProps({
        loading: {
            type: Boolean,
            default: false
        },
    })

</script>