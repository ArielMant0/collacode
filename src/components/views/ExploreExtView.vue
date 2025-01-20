<template>
    <v-sheet class="pa-0">
        <div v-if="!loading" style="width: 100%;" class="pa-2">
            <div class="mt-4 mb-8" style="overflow-x: auto;">
                <MetaItemsDimsBars/>
            </div>

        </div>
    </v-sheet>
</template>

<script setup>
    import MetaItemsDimsBars from '../meta_items/MetaItemDimsBars.vue';

    const props = defineProps({
        loading: {
            type: Boolean,
            default: false
        },
    })

</script>