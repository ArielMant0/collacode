<template>
    <v-sheet class="pa-0">
        <div style="width: 100%;" class="pa-2">
            <div v-if="!loading" class="mt-2 d-flex align-center flex-column">
                <TagUserDifferences v-if="app.users.length > 1" class="ml-2 mr-2"/>
                <div v-else>
                    There must be more than 1 coder to assess (dis)agreement
                </div>
            </div>
        </div>
    </v-sheet>
</template>

<script setup>
    import { useApp } from '@/store/app';
    import TagUserDifferences from '../tags/TagUserDifferences.vue';

    const app = useApp()
    const props = defineProps({
        loading: {
            type: Boolean,
            default: false
        },
    })
</script>