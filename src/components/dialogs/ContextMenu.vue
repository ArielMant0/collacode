<template>
    <v-sheet v-if="visible"
        class="pa-1"
        :style="{ position: 'absolute', top: clickY+'px', left: clickX+'px', 'z-index': 4999 }" border>
        <div ref="wrapper" class="d-flex flex-column text-caption">
            <div v-for="o in clickOptions" class="cursor-pointer pl-1 pr-1 onhover" @click="select(o)">{{ o }}</div>
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
        clickTarget,
        clickTargetId,
        clickData,
        clickX,
        clickY,
        clickOptions
    } = storeToRefs(settings)

    const wrapper = ref(null)
    const visible = computed(() => clickTargetId.value !== null)

    function getId(target) {
        if (target === clickTarget.value) {
            return clickTargetId.value
        }
        return clickData.value ? clickData.value[target] : null
    }

    function select(option) {
        switch(option) {
            case "edit tag":
                app.toggleEditTag(getId("tag"));
                break;
            case "delete tag":
                app.toggleDeleteTag(getId("tag"));
                break;
            case "add evidence":
                app.toggleAddEvidence(getId("game"), getId("tag"))
                break;
            case "edit evidence":
                app.toggleShowEvidence(getId("evidence"))
                break;
            case "delete evidence":
                app.toggleDeleteEvidence(getId("evidence"))
                break;
            case "add externalization":
                app.toggleAddExternalization(getId("game"), getId("group"), getId("tag"), getId("evidence"))
                break;
            case "edit externalization":
                app.toggleShowExternalization(getId("externalization"))
                break;
            case "delete externalization":
                app.toggleDeleteExternalization(getId("externalization"))
                break;
            case "add ext category":
                app.toggleAddExtCategory(getId("ext_category"), getId("parent"))
                break;
            case "edit ext category":
                app.toggleShowExtCategory(getId("ext_category"))
                break;
            case "delete ext category":
                app.toggleDeleteExtCategory(getId("ext_category"))
                break;
        }
        settings.setRightClick(null)
        emit("select", option);
    }

    function close() {
        settings.setRightClick(null)
        emit("cancel")
    }


    onMounted(() => {
        document.body.addEventListener("click", function(event) {
            if (wrapper.value && !wrapper.value.contains(event.target)) {
                settings.setRightClick(null)
            }
        });
    })
</script>

<style scoped>
.onhover:hover {
    background-color: lightgrey;
}
</style>