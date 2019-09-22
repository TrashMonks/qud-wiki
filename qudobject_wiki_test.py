from hagadias.gameroot import qindex
from qudobject_wiki import escape_ampersands


def test_escape_ampersands():
    assert escape_ampersands('&yfloating&G &Yglowsphere') == '&amp;yfloating&amp;G &amp;Yglowsphere'


def test_render_wiki_templates():
    """Test rendering the wiki template for each object to find any exceptions."""
    for name, obj in qindex.items():
        if obj.is_wiki_eligible():
            obj.wiki_template()


# Property tests
def test_ammodamagetypes():
    obj = qindex['Laser Rifle']
    assert obj.ammodamagetypes == 'Light</br>Heat'


def test_butcheredinto():
    # TODO: return corpse drop chances that are not given in ObjectBlueprints.xml,
    #  but rather in populationtables.xml:
    # obj = qindex['Albino ape corpse']
    # want = '{{corpse pop table|population=Albino ape corpse|'\
    #        'object=albino ape pelt|id=Albino Ape Pelt|num=1|weight=70}}</br>'\
    #        '{{corpse pop table|population=Albino ape corpse|'\
    #        ' object=albino ape heart|id=Albino Ape Heart|num=1|weight=10}}</br>'\
    #        '{{corpse pop table|population=Albino ape corpse|'\
    #        'object=ape fur cloak|id=Ape Fur Cloak|num=1|weight=20}}'
    # assert obj.butcheredinto == want
    obj = qindex['Boar Corpse']
    want = '{{Corpse pop table|population=Boar Corpse|' \
           'object={{ID to name|Raw Boar Meat}}|id=Raw Boar Meat}}'
    assert obj.butcheredinto == want


def test_colorstr():
    obj = qindex['SixDayStiltWall1']
    assert obj.colorstr == '&amp;y^c'


def test_cookeffect():
    obj = qindex['Freeze-Dried Hoarshrooms']
    assert obj.cookeffect == '{{CookEffect ID to name|cold}},{{CookEffect ID to name|fungus}}'


def test_corpse():
    obj = qindex['HindrenVillager']
    assert obj.corpse == '{{ID to name|Hindren Corpse}}'


def test_desc():
    obj = qindex['PhysicalObject']
    assert obj.desc is None
    obj = qindex['SalveTonic']
    assert obj.desc == """[True kin]
&amp;CDuration: 5 rounds
&amp;CYou recover 0.9 hit points per level (minimum 5) each round.

&amp;WThis item is a tonic. Applying one tonic while under the effects of another may produce undesired results.

[Mutant]
&amp;CDuration: 5 rounds
&amp;CYou recover 0.6 hit points per level (minimum 3) each round.

&amp;WThis item is a tonic. Applying one tonic while under the effects of another may produce undesired results."""  # noqa E501
    obj = qindex['BaseBear']
    assert obj.desc == """Only the familiar nursery rhyme courses through your brain.

The Grizzly Bear is huge and wild; 
It has devoured the infant child. 
The infant child is unaware;
It has been eaten by the bear."""  # noqa W291


def test_dynamictable():
    obj = qindex['AcidGasGrenade1']
    want = '{{Dynamic object|Grenades|AcidGasGrenade1}}'
    assert obj.dynamictable == want
    obj = qindex['Freeze-Dried Hoarshrooms']
    want = '{{Dynamic object|Jungle_Ingredients|Freeze-Dried Hoarshrooms}} </br>' \
           '{{Dynamic object|Ruins_Ingredients|Freeze-Dried Hoarshrooms}}'
    assert obj.dynamictable == want
    obj = qindex['Snapjaw Troglodyte']
    assert obj.dynamictable is None  # test {{{remove}}} as Value of DynamicObjectsTable:xxx


def test_extra():
    obj = qindex['MotorizedTreads']
    assert obj.extra == '{{Extra info|empsensitive = yes | metal = yes | savemodifier =' \
                        ' Move,Knockdown,Knockback,Restraint,Drag | savemodifieramt = 4}}'
    obj = qindex['Solar Condenser']
    assert obj.extra == '{{Extra info|empsensitive = yes | metal = yes | solid = yes |' \
                        ' flyover = no}}'


def test_gasemitted():
    obj = qindex['Defoliant Gas Pump']
    assert obj.gasemitted == '{{ID to name|DefoliantGas}}'


def test_harvestedinto():
    obj = qindex['Dreadroot']
    assert obj.harvestedinto == '{{ID to name|Dreadroot Tuber}}'


def test_inventory():
    obj = qindex['HindrenVillager']
    assert '{{inventory|LeatherBracer|1|no|100}}' in obj.inventory
    assert '{{inventory|Sandals|2|no|100}}' in obj.inventory
    assert '{{inventory|Vinewafer Sheaf|2-3|no|100}}' in obj.inventory
    assert '{{inventory|Iron Vinereaper|1|no|100}}' in obj.inventory


def test_mods():
    obj = qindex['Difucila']
    assert obj.mods == '{{ModID to name|ModSharp|1}} </br>{{ModID to name|ModMasterwork|1}}'
    obj = qindex['Caslainard']
    assert obj.mods == '{{ModID to name|ModCounterweighted|5}} </br>' \
                       '{{ModID to name|ModElectrified|7}}'


def test_mutations():
    obj = qindex['Girshworm']
    want = '{{creature mutation|{{MutationID to name|Regeneration}}|0|5}} </br>' \
           '{{creature mutation|{{MutationID to name|GasGenerationPoisonGas}}|1|5}} </br>' \
           '{{creature mutation|{{MutationID to name|DarkVision}}|3|5}}'
    assert obj.mutations == want


def test_oneat():
    obj = qindex['FireBreatherGland']
    want = '{{OnEat ID to name|BreatheOnEatFireBreather5}}'
    assert obj.oneat == want


def test_preservedinto():
    obj = qindex['FireBreatherGland']
    want = '{{ID to name|FireBreatherGlandPaste}}'
    assert obj.preservedinto == want


def test_renderstr():
    obj = qindex['EyelessCrabShell']
    assert obj.renderstr == '&#125;'  # not '}'


def test_reputationbonus():
    obj = qindex['Ape Fur Hat']
    want = '{{reputation bonus|{{FactionID to name|Apes}}|-100}}'
    assert obj.reputationbonus == want
    obj = qindex['Fork-Horned Helmet 3']
    want = '{{reputation bonus|{{FactionID to name|Antelopes}}|100}} </br>' \
           '{{reputation bonus|{{FactionID to name|Goatfolk}}|100}}'
    assert obj.reputationbonus == want
    obj = qindex['LuminousInfection']  # glowcrust
    want = '{{reputation bonus|{{FactionID to name|Fungi}}|200}} </br>' \
           '{{reputation bonus|{{FactionID to name|Consortium}}|-200}}'
    assert obj.reputationbonus == want


def test_weaponskill():
    obj = qindex['Gaslight Dagger']
    want = '{{SkillID to name|ShortBlades}}'
    assert obj.weaponskill == want
    obj = qindex['MasterworkCarbine']
    want = '{{SkillID to name|Rifle}}'
    assert obj.weaponskill == want
    obj = qindex['Fullerite Shield']
    want = '{{SkillID to name|Shield}}'
    assert obj.weaponskill == want
