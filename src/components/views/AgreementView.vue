<template>
    <v-sheet class="pa-0">
        <div style="width: 100%;" class="pa-2">
            <div v-if="!loading" class="mt-2 d-flex align-center flex-column">
                <TagUserDifferences class="ml-2 mr-2"/>
            </div>
        </div>
    </v-sheet>
</template>

<script setup>
    import TagUserDifferences from '../tags/TagUserDifferences.vue';

    const props = defineProps({
        loading: {
            type: Boolean,
            default: false
        },
    })
</script>