<template>
    <v-sheet class="pa-0">
        <div style="width: 100%;" class="pa-2">
            <div v-if="!loading" class="mt-2 d-flex align-center flex-column">
                <TagUserDifferences v-if="app.usersCanEdit.length > 1" :hidden="!active" class="ml-2 mr-2"/>
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
    import { useSettings } from '@/store/settings';
    import { computed } from 'vue';

    const app = useApp()
    const settings = useSettings()

    const props = defineProps({
        loading: {
            type: Boolean,
            default: false
        },
    })

    const active = computed(() => settings.activeTab === "agree")
</script>