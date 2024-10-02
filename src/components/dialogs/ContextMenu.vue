<template>
    <v-sheet v-if="visible"
        class="pa-1"
        :style="{ position: 'absolute', top: rightClickY+'px', left: rightClickX+'px', 'z-index': 4999 }" border>
        <div ref="wrapper" class="d-flex flex-column text-caption">
            <div v-for="o in rightClickOptions" class="cursor-pointer pl-1 pr-1 onhover" @click="select(o)">{{ o }}</div>
            <div class="mt-2 pl-1 pr-1 cursor-pointer onhover" @click="close"><i>cancel</i></div>
        </div>
    </v-sheet>
</template>

<script setup>
    import { useApp } from '@/store/app';
    import { useSettings } from '@/store/settings';
    import { storeToRefs } from 'pinia';
    import { computed, onMounted } from 'vue';

    const emit = defineEmits(["select", "cancel"])

    const app = useApp();
    const settings = useSettings();

    const {
        rightClickTag,
        rightClickGame,
        rightClickX,
        rightClickY,
        rightClickOptions
    } = storeToRefs(settings)

    const wrapper = ref(null)
    const visible = computed(() => rightClickTag.value || rightClickGame.value)

    function select(option) {
        switch(option) {
            case "edit tag":
                app.toggleEditTag(rightClickTag.value);
                break;
            case "add evidence":
                app.toggleAddEvidence(rightClickGame.value, rightClickTag.value)
                break;
            case "add externalization":
                app.toggleAddExternalization(rightClickGame.value, rightClickTag.value)
                break;
        }
        rightClickGame.value = null;
        rightClickTag.value = null;
        emit("select", option);
    }

    function close() {
        rightClickGame.value = null;
        rightClickTag.value = null;
        emit("cancel")
    }


    onMounted(() => {
        document.body.addEventListener("click", function(event) {
            if (wrapper.value && !wrapper.value.contains(event.target)) {
                settings.setRightClick(null, null)
            }
        });
    })
</script>

<style scoped>
.onhover:hover {
    background-color: lightgrey;
}
</style>