<template>
    <v-sheet ref="el" class="pa-0">
    <v-layout>
        <v-sheet class="pa-2" :min-width="expandNavDrawer ? 300 : 60">

            <v-btn @click="expandNavDrawer = !expandNavDrawer"
                :icon="expandNavDrawer ? 'mdi-arrow-left' : 'mdi-arrow-right'"
                block
                density="compact"
                rounded="sm"
                color="secondary"/>

            <v-divider class="mb-2 mt-2"></v-divider>

            <div v-if="!expandNavDrawer" class="d-flex flex-column align-center">
                <span v-if="transition" class="text-caption d-flex flex-column align-center">
                    <b>{{ app.getCodeName(transition.old_code) }}</b>
                    to
                    <b>{{ app.getCodeName(transition.new_code) }}</b>
                </span>
            </div>
            <div v-else>
                <v-select v-if="data.transitions"
                    v-model="transitionId"
                    :items="data.transitions"
                    class="mb-2"
                    density="compact"
                    hide-details
                    @update:model-value="setTransition"
                    item-title="name"
                    item-value="id"/>

            </div>
        </v-sheet>

        <div style="width: 100%;" class="pa-2">
            <CodingTransition v-if="transition"
                :time="myTime"
                :old-code="transition.old_code"
                :new-code="transition.new_code"
                :include-title="false"
                :edit="false"/>

            <div class="mt-2" style="width: 40%;">
                <GameEvidenceTiles v-if="transition" :time="myTime" :code="transition.new_code"/>
            </div>
        </div>
    </v-layout>
    </v-sheet>
</template>

<script setup>

    import { onMounted, reactive, computed, ref, watch } from 'vue';
    import CodingTransition from '@/components/CodingTransition.vue';
    import GameEvidenceTiles from '@/components/GameEvidenceTiles.vue';
    import { useApp } from '@/store/app';
    import { storeToRefs } from 'pinia';
    import { useSettings } from '@/store/settings';
    import DM from '@/use/data-manager';

    const app = useApp();
    const settings = useSettings();

    const props = defineProps({
        time: {
            type: Number,
            default: 0
        }
    });

    const myTime = ref(props.time);

    const el = ref(null);

    const { expandNavDrawer } = storeToRefs(settings)

    const transitionId = ref("")
    const transition = computed(() => data.transitions.find(d => d.id === transitionId.value))

    const data = reactive({ transitions: [], })

    function setTransition() {
        if (transition.value) {
            app.setActiveCode(transition.value.old_code);
            app.setTransitionCode(transition.value.new_code);
            app.needsReload("transition")
        }
    }

    function read() {
        if (DM.hasData("code_transitions")) {
            const trans = DM.getData("code_transitions");
            trans.forEach(d => d.name = `${app.getCodeName(d.old_code)} to ${app.getCodeName(d.new_code)}`)
            data.transitions = trans;
        }
    }

    onMounted(read)

    watch(() => props.time, function() {
        myTime.value = Date.now();
        if (!data.transitions || data.transitions.length === 0) {
            read();
        }
    })
    watch(() => app.activeCode, function() {
        if (app.activeCode !== transitionId.value) {
            transitionId.value = null;
        }
    })

</script>