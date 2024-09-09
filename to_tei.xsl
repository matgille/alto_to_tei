<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet xmlns:tei="http://www.tei-c.org/ns/1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
    xmlns:xs="http://www.w3.org/2001/XMLSchema" exclude-result-prefixes="xs" version="2.0"
    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:alto="http://www.loc.gov/standards/alto/ns-v4#">

    <xsl:param name="sigle"/>
    <xsl:param name="input_files"/>
    <xsl:param name="output_file"/>
    <xsl:param name="double_page"/>
    <xsl:variable name="MainZoneTag"
        select="(collection(concat($input_files, '?select=*.xml'))//alto:Tags/alto:OtherTag[@LABEL = 'MainZone']/@ID)[1]"/>
    <xsl:variable name="MarginTextZoneTag"
        select="collection(concat($input_files, '?select=*.xml'))//alto:Tags/alto:OtherTag[@LABEL = 'MarginTextZone']/@ID"/>
    <xsl:variable name="NumberingZoneTag"
        select="collection(concat($input_files, '?select=*.xml'))//alto:Tags/alto:OtherTag[@label = 'NumberingZone']/@id"/>
    <xsl:variable name="QuireMarksZoneTag"
        select="collection(concat($input_files, '?select=*.xml'))//alto:Tags/alto:OtherTag[@LABEL = 'QuireMarksZone']/@ID"/>
    <xsl:variable name="RunningTitleZoneTag"
        select="collection(concat($input_files, '?select=*.xml'))//alto:Tags/alto:OtherTag[@LABEL = 'RunningTitleZone']/@ID"/>
    <xsl:variable name="TitleZoneTag"
        select="collection(concat($input_files, '?select=*.xml'))//alto:Tags/alto:OtherTag[@LABEL = 'TitleZone']/@ID"/>
    <xsl:variable name="DropCapitalZoneTag"
        select="collection(concat($input_files, '?select=*.xml'))//alto:Tags/alto:OtherTag[@LABEL = 'DropCapitalZone']/@ID"/>
    <xsl:variable name="HeadingLine_rubricTag"
        select="collection(concat($input_files, '?select=*.xml'))//alto:Tags/alto:OtherTag[@LABEL = 'HeadingLine:rubric']/@ID"/>

    <xsl:strip-space elements="*"/>
    <xsl:output method="xml"/>

    <xsl:template match="/">
        <xsl:result-document href="{$output_file}">
            <xsl:comment><xsl:value-of select="$MainZoneTag"/></xsl:comment>
            <xsl:element name="TEI" namespace="http://www.tei-c.org/ns/1.0">
                <xsl:attribute name="xml:id" select="$sigle"/>
                <xsl:element name="teiHeader" namespace="http://www.tei-c.org/ns/1.0">
                    <xsl:element name="fileDesc" namespace="http://www.tei-c.org/ns/1.0">
                        <xsl:element name="titleStmt" namespace="http://www.tei-c.org/ns/1.0">
                            <xsl:element name="title" namespace="http://www.tei-c.org/ns/1.0">
                                <xsl:value-of select="$sigle"/>
                            </xsl:element>
                        </xsl:element>
                        <xsl:element name="publicationStmt" namespace="http://www.tei-c.org/ns/1.0">
                            <xsl:element name="p" namespace="http://www.tei-c.org/ns/1.0">Publication information</xsl:element>
                        </xsl:element>
                        <xsl:element name="sourceDesc" namespace="http://www.tei-c.org/ns/1.0">
                            <xsl:element name="p" namespace="http://www.tei-c.org/ns/1.0">Information about the
                                source</xsl:element>
                        </xsl:element>
                    </xsl:element>
                </xsl:element>
                <xsl:element name="facsimile" namespace="http://www.tei-c.org/ns/1.0"/>
                <xsl:element name="text" namespace="http://www.tei-c.org/ns/1.0">
                    <xsl:element name="body" namespace="http://www.tei-c.org/ns/1.0">
                        <xsl:element name="div" namespace="http://www.tei-c.org/ns/1.0">
                            <xsl:for-each select="collection(concat($input_files, '?select=*.xml'))">
                                <!--On attend ici que les ALTO se trouvent dans un fichier au nom du sigle choisi.-->
                                <xsl:sort select="substring-before(substring-after(base-uri(), concat($sigle, '/')), '.xml')" data-type="number"/>
                                <xsl:message>
                                    <xsl:message>TEST</xsl:message>
                                    <xsl:value-of select="base-uri()"/>
                                </xsl:message>
                                <xsl:variable name="folio">
                                    <xsl:value-of select="substring-before(substring-after(base-uri(), 'in/'), '.xml')"/>
                                </xsl:variable>
                                <xsl:element name="pb" namespace="http://www.tei-c.org/ns/1.0">
                                    <xsl:attribute name="n">
                                        <xsl:value-of select="$folio"/>
                                    </xsl:attribute>
                                    <xsl:attribute name="facs">
                                        <xsl:value-of
                                            select="concat($input_files, //alto:sourceImageInformation/alto:fileName)"
                                        />
                                    </xsl:attribute>
                                </xsl:element>
                                <xsl:apply-templates select="descendant::alto:alto"/>
                            </xsl:for-each>
                        </xsl:element>
                    </xsl:element>
                </xsl:element>
            </xsl:element>
        </xsl:result-document>
    </xsl:template>

    <xsl:template match="alto:Description"/>

    <xsl:template match="alto:alto">
        <xsl:apply-templates/>
    </xsl:template>

    <xsl:template match="alto:PrintSpace">
        <!--Depuis eScriptorium l'export ALTO pose problème du point de vue de l'ordre des colonnes: 
        https://gitlab.com/scripta/escriptorium/-/issues/373-->
        <!--On va donc aller rétablir l'ordre en prenant la position du début de chaque zone de texte (point supérieur gauche)-->
        <!--Merci à Simon Gabay pour cette suggestion-->
        <xsl:apply-templates select="descendant::alto:TextBlock">
            <xsl:sort select="@HPOS" data-type="number"/>
        </xsl:apply-templates>

    </xsl:template>



    <xsl:template match="alto:tags">
        <!--Ici on peut se servir de la typologie pour créer une typologie dans le tei:teiHeader-->
    </xsl:template>

    <xsl:template match="alto:TextBlock[@TAGREFS = $MainZoneTag]">
        <!--On remet en place les tei:cb-->
        <xsl:choose>
            <xsl:when test="$double_page = 'True'">
                <!--En mode double page-->
                <xsl:choose>
                    <xsl:when test="count(preceding::alto:TextBlock[@TAGREFS = $MainZoneTag]) = 2">
                        <!--Quand la colonne en cours est la troisième on crée un élément tei:pb-->
                        <xsl:variable name="folio">
                            <xsl:value-of select="substring-before(substring-after(base-uri(), concat($sigle, '/')), '.xml')"/>
                        </xsl:variable>
                        <xsl:element name="pb" namespace="http://www.tei-c.org/ns/1.0">
                            <xsl:attribute name="n">
                                <xsl:value-of select="$folio"/>
                            </xsl:attribute>
                            <xsl:attribute name="facs">
                                <xsl:value-of
                                    select="concat($input_files, //alto:sourceImageInformation/alto:fileName)"
                                />
                            </xsl:attribute>
                        </xsl:element>
                    </xsl:when>
                    <xsl:otherwise>
                        <!-- Si ce n'est pas la troisième on crée un élément tei:cb-->
                        <xsl:if test="preceding::alto:TextBlock[@TAGREFS = $MainZoneTag]">
                            <xsl:element name="cb" namespace="http://www.tei-c.org/ns/1.0">
                                <xsl:attribute name="break">?</xsl:attribute>
                            </xsl:element>
                        </xsl:if>
                    </xsl:otherwise>
                </xsl:choose>
            </xsl:when>
            <xsl:otherwise>
                <!--Mode page simple-->
                <xsl:if test="preceding::alto:TextBlock[@TAGREFS = $MainZoneTag]">
                    <xsl:element name="cb" namespace="http://www.tei-c.org/ns/1.0">
                        <xsl:attribute name="break">?</xsl:attribute>
                    </xsl:element>
                </xsl:if>
            </xsl:otherwise>
        </xsl:choose>
        <xsl:apply-templates/>
    </xsl:template>

    <xsl:template match="alto:TextBlock[@TAGREFS = $QuireMarksZoneTag]">
        <xsl:element name="fw" namespace="http://www.tei-c.org/ns/1.0">
            <xsl:attribute name="type">reclame</xsl:attribute>
            <xsl:apply-templates/>
        </xsl:element>
    </xsl:template>



    <xsl:template match="alto:TextBlock[@TAGREFS = $MarginTextZoneTag]">
        <xsl:element name="add" namespace="http://www.tei-c.org/ns/1.0">
            <xsl:attribute name="type">ajout</xsl:attribute>
            <xsl:attribute name="place">?</xsl:attribute>
            <xsl:attribute name="facs">
                <xsl:value-of select="descendant::alto:Polygon/@POINTS"/>
            </xsl:attribute>
            <xsl:apply-templates/>
        </xsl:element>
    </xsl:template>



    <!--<xsl:template match="alto:TextBlock[@TAGREFS = 'LT6']">
        <xsl:element name="add" namespace="http://www.tei-c.org/ns/1.0">
            <xsl:attribute name="type">glose</xsl:attribute>
            <xsl:attribute name="place">?</xsl:attribute>
            <xsl:attribute name="facs">
                <xsl:value-of select="descendant::alto:Polygon/@POINTS"/>
            </xsl:attribute>
        </xsl:element>
    </xsl:template>-->



    <!--<xsl:template match="alto:TextBlock[@TAGREFS = 'BT28']">
        <xsl:element name="add" namespace="http://www.tei-c.org/ns/1.0">
            <xsl:attribute name="type">margin</xsl:attribute>
            <xsl:attribute name="facs">
                <xsl:value-of select="descendant::alto:Polygon/@POINTS"/>
            </xsl:attribute>
            <xsl:apply-templates/>
        </xsl:element>
    </xsl:template>-->

    <xsl:template match="alto:TextBlock[@TAGREFS = $DropCapitalZoneTag]">
        <xsl:element name="graphic" namespace="http://www.tei-c.org/ns/1.0">
            <xsl:attribute name="type">initiale</xsl:attribute>
            <xsl:attribute name="facs">
                <xsl:value-of select="descendant::alto:Polygon/@POINTS"/>
            </xsl:attribute>
        </xsl:element>
    </xsl:template>

    <xsl:template match="alto:TextBlock[@TAGREFS = $RunningTitleZoneTag]">
        <xsl:element name="fw" namespace="http://www.tei-c.org/ns/1.0">
            <xsl:attribute name="type">titre_courant</xsl:attribute>
            <xsl:apply-templates/>
        </xsl:element>
    </xsl:template>



    <xsl:template match="alto:TextBlock[@TAGREFS = $NumberingZoneTag]">
        <xsl:element name="fw" namespace="http://www.tei-c.org/ns/1.0">
            <xsl:attribute name="type">numerotation</xsl:attribute>
            <xsl:apply-templates/>
        </xsl:element>
    </xsl:template>


    <xsl:template match="alto:TextBlock[not(@TAGREFS)]">
        <!--        <xsl:element name="ab" namespace="http://www.tei-c.org/ns/1.0">-->
        <!--            <xsl:attribute name="type">untyped</xsl:attribute>-->
        <!--            <xsl:apply-templates/>-->
        <!--        </xsl:element>-->
    </xsl:template>




    <xsl:template match="alto:TextLine">
        <xsl:element name="lb" namespace="http://www.tei-c.org/ns/1.0">
            <xsl:attribute name="break">?</xsl:attribute>
            <xsl:if test="@TAGREFS = $HeadingLine_rubricTag">
                <xsl:attribute name="rend">rubric</xsl:attribute>
            </xsl:if>
            <xsl:attribute name="facs">
                <xsl:value-of select="descendant::alto:Polygon/@POINTS"/>
            </xsl:attribute>
            <xsl:attribute name="xml:id">
                <xsl:value-of select="@ID"/>
            </xsl:attribute>
        </xsl:element>
        <xsl:value-of select="replace(alto:String/@CONTENT, '\s$', '')"/>
    </xsl:template>

</xsl:stylesheet>
