<template>
    <v-sheet ref="el" class="pa-0">
        <div v-if="!loading" class="pa-2" style="width: 100%;">
            <div v-if="activeTransition" class="d-flex flex-column">
                <TransitionHistory/>
                <CodingTransition :old-code="oldCode" :new-code="newCode"/>
            </div>
        </div>
    </v-sheet>
</template>

<script setup>
    import CodingTransition from '@/components/CodingTransition.vue';

    import { useApp } from '@/store/app'
    import { storeToRefs } from 'pinia'
    import { ref } from 'vue'

    const app = useApp()

    const { activeTransition, oldCode, newCode } = storeToRefs(app);

    const props = defineProps({
        loading: {
            type: Boolean,
            default: false
        },
        size: {
            type: Number,
            default: 1000
        }
    })

    const el = ref(null);


</script>
