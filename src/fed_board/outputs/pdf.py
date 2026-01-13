"""PDF generator for FOMC meeting minutes in official Fed format."""

import re
from pathlib import Path

from weasyprint import CSS, HTML

from fed_board.agents.personas import FOMC_MEMBERS, get_voting_members
from fed_board.config import Settings, get_settings
from fed_board.models.meeting import MeetingResult
from fed_board.models.member import Role
from fed_board.outputs.minutes import MinutesGenerator


# CSS styling to match Fed official documents
FED_STYLE_CSS = """
@page {
    size: letter;
    margin: 1in 1in 1in 1in;
    @top-center {
        content: counter(page) "    " string(meeting-date);
        font-family: "Georgia", "Times New Roman", Times, serif;
        font-size: 9pt;
        color: #333;
    }
}

@page:first {
    @top-center {
        content: none;
    }
}

body {
    font-family: "Georgia", "Times New Roman", Times, serif;
    font-size: 11pt;
    line-height: 1.7;
    color: #000;
    max-width: 100%;
}

h1 {
    font-family: "Georgia", "Times New Roman", Times, serif;
    font-size: 24pt;
    font-weight: normal;
    color: #003366;
    text-align: left;
    margin-top: 0;
    margin-bottom: 6pt;
    border-bottom: none;
}

.meeting-date {
    font-family: "Georgia", "Times New Roman", Times, serif;
    font-size: 14pt;
    font-weight: normal;
    color: #003366;
    text-align: left;
    margin-bottom: 18pt;
    string-set: meeting-date content();
}

h2 {
    font-family: "Georgia", "Times New Roman", Times, serif;
    font-size: 14pt;
    font-weight: normal;
    font-style: normal;
    color: #003366;
    margin-top: 24pt;
    margin-bottom: 12pt;
    border-bottom: none;
}

h3 {
    font-size: 11pt;
    font-weight: bold;
    margin-top: 12pt;
    margin-bottom: 6pt;
}

p {
    text-align: justify;
    margin-bottom: 12pt;
    text-indent: 0;
}

.section-content p {
    text-indent: 0.3in;
}

.section-content p:first-of-type {
    text-indent: 0;
}

.opening-paragraph {
    text-indent: 0;
    margin-bottom: 18pt;
}

hr {
    display: none;
}

ul, ol {
    margin-left: 0.3in;
    margin-bottom: 12pt;
}

li {
    margin-bottom: 6pt;
}

strong {
    font-weight: bold;
}

em {
    font-style: italic;
}

.voting-section {
    margin-top: 18pt;
}

.voting-for, .voting-against {
    margin-bottom: 10pt;
}

.attendance-section {
    margin-top: 36pt;
    page-break-before: always;
}

.attendance-section h2 {
    font-style: normal;
    text-align: center;
    margin-bottom: 18pt;
}

.attendance-group {
    margin-bottom: 12pt;
}

.attendance-group-title {
    font-style: italic;
    margin-bottom: 6pt;
}

.footnote {
    font-size: 9pt;
    margin-top: 24pt;
    border-top: 1px solid #666;
    padding-top: 8pt;
}

.footnote sup {
    font-size: 8pt;
}

.secretary-signature {
    margin-top: 36pt;
    text-align: center;
}

.secretary-signature p {
    text-align: center;
    text-indent: 0;
}

.disclaimer {
    margin-top: 36pt;
    padding: 12pt;
    border: 1px solid #ccc;
    background-color: #f5f5f5;
    font-size: 9pt;
}

.disclaimer-title {
    font-size: 10pt;
    font-weight: bold;
    margin-bottom: 8pt;
    color: #666;
}

.directive-quote {
    margin: 14pt 0.5in;
    font-size: 10pt;
}

blockquote {
    margin-left: 0.5in;
    margin-right: 0.5in;
    font-style: normal;
    padding-left: 0;
}

sup {
    font-size: 8pt;
    vertical-align: super;
}
"""


class PDFGenerator:
    """Generates PDF meeting minutes in official Fed format."""

    def __init__(self, settings: Settings | None = None) -> None:
        """
        Initialize the PDF generator.

        Args:
            settings: Application settings
        """
        self.settings = settings or get_settings()
        self.minutes_generator = MinutesGenerator(settings)

    def generate_html(self, result: MeetingResult) -> str:
        """
        Generate HTML for PDF conversion in official Fed minutes format.

        Args:
            result: The meeting result

        Returns:
            HTML string matching Fed minutes structure
        """
        meeting = result.meeting
        decision = result.decision
        year = meeting.meeting_date.year

        # Get voting members for this year
        voting_members = get_voting_members(year)

        # Build opening paragraph
        opening = self._build_opening_paragraph(meeting)

        # Build all sections
        financial_markets = self._build_financial_markets_section(result)
        staff_economic = self._build_staff_economic_section(result)
        staff_financial = self._build_staff_financial_section(result)
        staff_outlook = self._build_staff_outlook_section(result)
        participants_views = self._build_participants_views_section(result)
        policy_actions = self._build_policy_actions_section(result)
        voting_section = self._build_voting_section(result)
        attendance_section = self._build_attendance_section(result, year)

        html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>FOMC Minutes - {meeting.display_date}</title>
</head>
<body>
    <h1>Minutes of the Federal Open Market Committee</h1>
    <p class="meeting-date">{meeting.display_date}</p>

    <p class="opening-paragraph">{opening}</p>

    <h2>Developments in Financial Markets and Open Market Operations</h2>
    <div class="section-content">
        {financial_markets}
    </div>

    <h2>Staff Review of the Economic Situation</h2>
    <div class="section-content">
        {staff_economic}
    </div>

    <h2>Staff Review of the Financial Situation</h2>
    <div class="section-content">
        {staff_financial}
    </div>

    <h2>Staff Economic Outlook</h2>
    <div class="section-content">
        {staff_outlook}
    </div>

    <h2>Participants' Views on Current Conditions and the Economic Outlook</h2>
    <div class="section-content">
        {participants_views}
    </div>

    <h2>Committee Policy Actions</h2>
    <div class="section-content">
        {policy_actions}
    </div>

    <div class="voting-section">
        {voting_section}
    </div>

    {attendance_section}

    <div class="secretary-signature">
        <p>_______________________</p>
        <p>Secretary of the Federal Open Market Committee</p>
    </div>

    <div class="disclaimer">
        <p class="disclaimer-title">AI-GENERATED SIMULATION NOTICE</p>
        <p>
            This document was generated by an AI simulation system (Fed Decision Board)
            using {result.model_used} and does not represent actual Federal Reserve
            decisions, policy, or official communications. The content is produced for
            educational, research, and analytical purposes only. Any resemblance to
            actual FOMC deliberations is simulated based on publicly available information
            about member positions and economic conditions.
        </p>
        <p><em>Generated: {result.created_at.strftime('%B %d, %Y at %H:%M:%S')}</em></p>
    </div>
</body>
</html>
"""
        return html

    def _build_opening_paragraph(self, meeting) -> str:
        """Build the official opening paragraph."""
        if meeting.meeting_end_date:
            start_date = meeting.meeting_date.strftime("%A, %B %d, %Y")
            end_date = meeting.meeting_end_date.strftime("%A, %B %d, %Y")
            return (
                f"A joint meeting of the Federal Open Market Committee and the Board of "
                f"Governors of the Federal Reserve System was held in the offices of the "
                f"Board of Governors on {start_date}, at 10:00 a.m. and continued on "
                f"{end_date}, at 9:00 a.m.<sup>1</sup>"
            )
        else:
            date_str = meeting.meeting_date.strftime("%A, %B %d, %Y")
            return (
                f"A joint meeting of the Federal Open Market Committee and the Board of "
                f"Governors of the Federal Reserve System was held in the offices of the "
                f"Board of Governors on {date_str}, at 10:00 a.m.<sup>1</sup>"
            )

    def _build_financial_markets_section(self, result: MeetingResult) -> str:
        """Build the financial markets and open market operations section."""
        decision = result.decision
        impact = result.market_impact

        # Describe treasury movements
        if impact:
            if impact.treasury_10y_change_bps > 5:
                treasury_desc = "increased modestly"
            elif impact.treasury_10y_change_bps < -5:
                treasury_desc = "declined"
            else:
                treasury_desc = "were little changed, on net,"

            if impact.sp500_change_pct > 1:
                equity_desc = "advanced"
            elif impact.sp500_change_pct < -1:
                equity_desc = "declined"
            else:
                equity_desc = "were little changed, on net,"
        else:
            treasury_desc = "remained within recent ranges"
            equity_desc = "were little changed, on net,"

        return f"""
        <p>The manager turned first to an overview of broad market developments during
        the intermeeting period. Market participants continued to interpret incoming
        economic data as consistent with a resilient economy. Investors' expectations
        for the path of the policy rate were attentive to evolving economic conditions
        and Federal Reserve communications.</p>

        <p>The manager turned next to developments in Treasury markets. Treasury yields
        {treasury_desc} over the intermeeting period. Market-based measures of inflation
        compensation showed modest movements, reflecting market participants' assessments
        of the inflation outlook and monetary policy expectations.</p>

        <p>Broad equity price indexes {equity_desc} over the intermeeting period. Equity
        prices showed sensitivity to economic data releases and policymaker communications.
        Corporate credit spreads remained at relatively tight levels, suggesting continued
        investor confidence in corporate credit quality.</p>

        <p>Regarding international developments, the trade-weighted dollar index showed
        modest movements over the intermeeting period. Foreign central bank policy
        expectations continued to evolve in response to global economic conditions.</p>

        <p>By unanimous vote, the Committee ratified the Desk's domestic transactions
        over the intermeeting period. There were no intervention operations in foreign
        currencies for the System's account during the intermeeting period.</p>
        """

    def _build_staff_economic_section(self, result: MeetingResult) -> str:
        """Build the staff review of economic situation section."""
        # Use the AI-generated economic outlook as base
        outlook_text = result.economic_outlook if result.economic_outlook else ""

        # Build a comprehensive section
        paragraphs = []

        paragraphs.append(
            "<p>The information available at the time of the meeting indicated that "
            "economic activity had continued to expand. Labor market conditions remained "
            "solid, with payroll gains continuing and the unemployment rate staying at "
            "historically low levels. Consumer price inflation remained above the "
            "Committee's 2 percent longer-run objective.</p>"
        )

        if outlook_text:
            # Format the AI-generated content
            formatted = self._format_paragraphs(outlook_text)
            paragraphs.append(formatted)

        paragraphs.append(
            "<p>The unemployment rate remained at low levels by historical standards. "
            "The pace of payroll employment gains continued at a solid rate. Other "
            "available labor market indicators—such as initial claims for unemployment "
            "insurance benefits, rates of job openings and layoffs, and survey measures "
            "of labor market conditions—were consistent with a labor market that remained "
            "tight but was gradually coming into better balance.</p>"
        )

        paragraphs.append(
            "<p>Total consumer price inflation—as measured by the 12-month change in the "
            "price index for personal consumption expenditures (PCE)—remained above the "
            "Committee's 2 percent objective. Core PCE price inflation, which excludes "
            "changes in consumer energy prices and many consumer food prices, also "
            "remained elevated relative to the Committee's goal.</p>"
        )

        return "\n".join(paragraphs)

    def _build_staff_financial_section(self, result: MeetingResult) -> str:
        """Build the staff review of financial situation section."""
        return """
        <p>Over the intermeeting period, nominal Treasury yields showed modest movements
        as market participants assessed incoming economic data and implications for
        monetary policy. Changes in nominal yields reflected movements in both real
        yields and inflation compensation.</p>

        <p>In domestic credit markets, conditions remained generally supportive for
        businesses and households. Financing conditions were somewhat restrictive for
        some borrowers, particularly in sectors sensitive to interest rates. Large
        businesses continued to access credit markets at a solid pace.</p>

        <p>Credit performance remained stable in most markets. Delinquency rates for
        consumer loans remained elevated in some categories but showed signs of
        stabilization. Commercial real estate credit conditions continued to warrant
        close monitoring given the ongoing adjustments in that sector.</p>

        <p>Bank lending standards remained somewhat tight across most loan categories,
        while loan demand showed mixed signals. Market-based financing remained available
        for investment-grade borrowers at favorable terms.</p>
        """

    def _build_staff_outlook_section(self, result: MeetingResult) -> str:
        """Build the staff economic outlook section."""
        return """
        <p>The staff projection for the U.S. economy anticipated continued moderate
        growth in real GDP. The projection incorporated the assumption that financial
        conditions would remain generally supportive of economic expansion while
        monetary policy worked to bring inflation back to the Committee's 2 percent
        objective.</p>

        <p>The staff's inflation forecast anticipated a gradual return toward the
        Committee's 2 percent longer-run objective, although the path was expected
        to be uneven. Core inflation was projected to moderate as supply and demand
        conditions continued to come into better balance.</p>

        <p>The staff continued to judge that uncertainty around the baseline projection
        remained elevated. Risks around the forecast for real activity were seen as
        roughly balanced. Risks around the inflation forecast remained tilted to the
        upside, given the possibility that inflation could prove more persistent than
        expected.</p>
        """

    def _build_participants_views_section(self, result: MeetingResult) -> str:
        """Build the participants' views section in impersonal Fed style."""
        decision = result.decision

        # Analyze vote preferences to determine sentiment distribution
        hawk_count = sum(
            1 for v in result.vote_preferences
            if v.preferred_rate_change > 0 or "inflation" in v.reasoning.lower()
        )
        dove_count = sum(
            1 for v in result.vote_preferences
            if v.preferred_rate_change < 0 or "employment" in v.reasoning.lower()
        )
        total = len(result.vote_preferences) if result.vote_preferences else 12

        paragraphs = []

        # Opening observation - economic activity
        paragraphs.append(
            "<p>In their discussion of current conditions and the economic outlook, "
            "participants noted that recent indicators suggested that economic activity "
            "had continued to expand at a solid pace. Several participants observed that "
            "consumer spending remained resilient, supported by solid labor income growth "
            "and household balance sheets. A few participants noted that business fixed "
            "investment had shown mixed signals, with strength in some sectors offset by "
            "weakness in others.</p>"
        )

        # Inflation discussion - varies based on hawk/dove balance
        if hawk_count > dove_count:
            inflation_text = (
                "<p>Participants observed that inflation remained above the Committee's "
                "2 percent objective. Most participants noted concerns about the persistence "
                "of elevated inflation and emphasized the importance of returning inflation "
                "to the Committee's goal in a timely manner. Several participants observed "
                "that while headline inflation had moderated somewhat, core inflation "
                "remained elevated, particularly in services categories. A few participants "
                "noted that the pace of disinflation had slowed in recent months.</p>"
            )
        elif dove_count > hawk_count:
            inflation_text = (
                "<p>Participants observed that inflation remained somewhat above the "
                "Committee's 2 percent objective but had continued to moderate. Several "
                "participants noted that the disinflation process was proceeding broadly "
                "as expected, with goods prices declining and services inflation gradually "
                "easing. A few participants observed that longer-term inflation expectations "
                "remained well anchored, which supported the view that inflation would "
                "continue to move toward the Committee's goal.</p>"
            )
        else:
            inflation_text = (
                "<p>Participants observed that inflation remained above the Committee's "
                "2 percent objective. Most participants noted that while inflation had "
                "moved down from its peak, the pace of disinflation had been uneven. "
                "Several participants emphasized the importance of remaining vigilant "
                "about inflation risks, while others noted that progress toward the "
                "inflation objective was continuing.</p>"
            )
        paragraphs.append(inflation_text)

        # Labor market discussion
        paragraphs.append(
            "<p>With regard to the labor market, participants observed that conditions "
            "remained solid. Several participants noted that labor demand and supply "
            "had continued to come into better balance, as evidenced by a moderation "
            "in job openings and a gradual uptick in the unemployment rate from very "
            "low levels. Participants generally agreed that the labor market remained "
            "strong by historical standards but was no longer contributing to "
            "inflationary pressures to the same degree as in the past.</p>"
        )

        # Economic outlook and risks
        paragraphs.append(
            "<p>In discussing the outlook, participants generally expected that, with "
            "an appropriate stance of monetary policy, inflation would continue to move "
            "toward the Committee's 2 percent objective while the labor market remained "
            "solid. Participants noted that uncertainty about the economic outlook "
            "remained elevated. Several participants emphasized that risks to the outlook "
            "were roughly balanced, while a few participants judged that downside risks "
            "to employment had increased or that upside risks to inflation remained.</p>"
        )

        # Policy discussion based on decision
        if decision.rate_change_bps > 0:
            policy_text = (
                "<p>In their consideration of monetary policy at this meeting, "
                "participants judged that it would be appropriate to raise the target "
                "range for the federal funds rate. Most participants agreed that "
                "elevated inflation warranted a continued restrictive stance of "
                "monetary policy. Several participants noted that the Committee "
                "should remain prepared to adjust policy as needed based on incoming "
                "data. A few participants expressed the view that the Committee should "
                "be attentive to the risk of tightening too much.</p>"
            )
        elif decision.rate_change_bps < 0:
            policy_text = (
                "<p>In their consideration of monetary policy at this meeting, "
                "participants agreed that inflation had made progress toward the "
                "Committee's 2 percent objective and that risks to achieving the "
                "Committee's employment and inflation goals had moved into better "
                "balance. Most participants supported lowering the target range for "
                "the federal funds rate at this meeting. Several participants noted "
                "that a reduction in policy restraint was appropriate given the "
                "progress on inflation and the current level of rates. A few "
                "participants expressed the view that the Committee should proceed "
                "cautiously in reducing policy restraint.</p>"
            )
        else:
            policy_text = (
                "<p>In their consideration of monetary policy at this meeting, "
                "participants generally agreed that the current stance of monetary "
                "policy remained appropriate. Most participants noted that it would "
                "be prudent to maintain the current level of the federal funds rate "
                "while continuing to assess incoming data. Several participants "
                "emphasized that the Committee should remain data dependent and "
                "prepared to adjust policy as warranted. A few participants noted "
                "the importance of clearly communicating the Committee's reaction "
                "function to the public.</p>"
            )
        paragraphs.append(policy_text)

        return "\n".join(paragraphs)

    def _build_policy_actions_section(self, result: MeetingResult) -> str:
        """Build the committee policy actions section in Fed style."""
        decision = result.decision

        # Determine the action description
        if decision.rate_change_bps > 0:
            action_desc = f"raise the target range for the federal funds rate by {decision.rate_change_bps} basis points"
            vote_count = result.vote_count_for
        elif decision.rate_change_bps < 0:
            action_desc = f"lower the target range for the federal funds rate by {abs(decision.rate_change_bps)} basis points"
            vote_count = result.vote_count_for
        else:
            action_desc = "maintain the target range for the federal funds rate"
            vote_count = result.vote_count_for

        paragraphs = []

        # Opening observations
        paragraphs.append(
            "<p>In their discussion of monetary policy for this meeting, members "
            "agreed that recent indicators suggested that economic activity had continued "
            "to expand at a solid pace. They also agreed that job gains had remained "
            "solid and that the unemployment rate had stayed at low levels. Members "
            "observed that inflation remained somewhat above the Committee's 2 percent "
            "longer-run goal.</p>"
        )

        # Risk assessment
        paragraphs.append(
            "<p>Members noted that the economic outlook remained uncertain and that "
            "the Committee remained attentive to the risks to both sides of its dual "
            "mandate. Members emphasized that the Committee's decisions would continue "
            "to be based on careful assessment of incoming data, the evolving outlook, "
            "and the balance of risks.</p>"
        )

        # Policy decision
        paragraphs.append(
            f"<p>In support of the Committee's goals of maximum employment and inflation "
            f"at the rate of 2 percent over the longer run, members agreed to {action_desc}, "
            f"to {decision.rate_range_str}. Members agreed that, in considering the extent "
            f"and timing of additional adjustments to the target range for the federal "
            f"funds rate, the Committee would carefully assess incoming data, the evolving "
            f"outlook, and the balance of risks.</p>"
        )

        # Forward guidance
        paragraphs.append(
            "<p>Members agreed that the Committee's assessments would take into account "
            "a wide range of information, including readings on labor market conditions, "
            "inflation pressures and inflation expectations, and financial and "
            "international developments. Members reaffirmed the Committee's strong "
            "commitment to returning inflation to its 2 percent objective.</p>"
        )

        return "\n".join(paragraphs)

    def _build_dissent_paragraph(self, result: MeetingResult) -> str:
        """Build paragraph describing dissents."""
        dissents = []
        for analysis in result.dissent_analyses:
            dissents.append(
                f"{analysis.dissenter_name}, who preferred {analysis.dissenter_preference}"
            )

        if len(dissents) == 1:
            dissent_text = dissents[0]
        else:
            dissent_text = ", ".join(dissents[:-1]) + ", and " + dissents[-1]

        return f"<p>Voting against this action: {dissent_text}.</p>"

    def _build_voting_section(self, result: MeetingResult) -> str:
        """Build the voting section with member names."""
        decision = result.decision

        # Get voters for and against
        for_voters = [v.member_name for v in result.votes if v.vote_for_decision]
        against_voters = [v for v in result.votes if not v.vote_for_decision]

        # Determine action text
        if decision.rate_change_bps > 0:
            action = f"raise the target range for the federal funds rate by {decision.rate_change_bps} basis points to {decision.rate_range_str}"
        elif decision.rate_change_bps < 0:
            action = f"lower the target range for the federal funds rate by {abs(decision.rate_change_bps)} basis points to {decision.rate_range_str}"
        else:
            action = f"maintain the target range for the federal funds rate at {decision.rate_range_str}"

        if for_voters:
            html = f"<p><strong>Voting for this action:</strong> {'; '.join(for_voters)}.</p>\n"
        else:
            html = "<p><strong>Voting for this action:</strong> None.</p>\n"

        if against_voters:
            against_names = []
            for v in against_voters:
                reason = ""
                if v.preferred_rate > decision.new_rate_upper:
                    reason = f"who preferred to raise rates further"
                elif v.preferred_rate < decision.new_rate_lower:
                    reason = f"who preferred a larger rate reduction"
                else:
                    reason = f"who preferred a different policy action"
                against_names.append(f"{v.member_name}, {reason}")

            html += f"<p><strong>Voting against this action:</strong> {'; '.join(against_names)}.</p>\n"
        else:
            html += "<p><strong>Voting against this action:</strong> None.</p>\n"

        return html

    def _build_attendance_section(self, result: MeetingResult, year: int) -> str:
        """Build the attendance section listing all participants."""
        # Separate members by role
        chair = None
        vice_chair = None
        vice_chair_supervision = None
        governors = []
        ny_president = None
        voting_presidents = []
        non_voting_presidents = []

        for member in FOMC_MEMBERS:
            if member.role == Role.CHAIR:
                chair = member
            elif member.role == Role.VICE_CHAIR:
                vice_chair = member
            elif member.role == Role.VICE_CHAIR_SUPERVISION:
                vice_chair_supervision = member
            elif member.role == Role.GOVERNOR:
                governors.append(member)
            elif member.role == Role.PRESIDENT:
                if "New York" in member.bank:
                    ny_president = member
                elif member.is_voting_in_year(year):
                    voting_presidents.append(member)
                else:
                    non_voting_presidents.append(member)

        html = """
        <div class="attendance-section">
            <h2>Attendance</h2>
        """

        # Chair and Vice Chairs
        if chair:
            html += f"<p>{chair.name}, Chair</p>\n"
        if vice_chair:
            html += f"<p>{vice_chair.name}, Vice Chair</p>\n"
        if vice_chair_supervision:
            html += f"<p>{vice_chair_supervision.name}, Vice Chair for Supervision</p>\n"

        # Governors
        if governors:
            gov_names = ", ".join([g.name for g in governors])
            html += f"<p>{gov_names}, Governors</p>\n"

        # NY Fed President
        if ny_president:
            html += f"<p>{ny_president.name}, President, Federal Reserve Bank of New York</p>\n"

        # Voting Reserve Bank Presidents
        if voting_presidents:
            html += "<p class='attendance-group-title'>Voting Reserve Bank Presidents:</p>\n"
            for pres in voting_presidents:
                bank_name = pres.bank.replace("Federal Reserve Bank of ", "")
                html += f"<p>{pres.name}, President, {bank_name}</p>\n"

        # Non-voting Reserve Bank Presidents (Alternate Members)
        if non_voting_presidents:
            html += "<p class='attendance-group-title'>Alternate Members of the Committee:</p>\n"
            alt_names = ", ".join([p.name for p in non_voting_presidents[:4]])  # Show first 4
            html += f"<p>{alt_names}</p>\n"

        html += """
            <div class="footnote">
                <p><sup>1</sup> This AI simulation represents a hypothetical FOMC meeting
                based on the economic conditions and member characteristics as of the
                simulation date. Attendance reflects the current FOMC composition.</p>
            </div>
        </div>
        """

        return html

    def _get_action_text(self, decision) -> str:
        """Get action text for the decision."""
        if decision.rate_change_bps > 0:
            return "raise"
        elif decision.rate_change_bps < 0:
            return "lower"
        return "maintain"

    def _format_paragraphs(self, text: str) -> str:
        """Format text into HTML paragraphs."""
        if not text:
            return ""

        paragraphs = text.split("\n\n")
        html_paragraphs = []
        for p in paragraphs:
            p = p.strip()
            if p:
                # Handle markdown-style bold
                p = re.sub(r'\*\*([^*]+)\*\*', r'<strong>\1</strong>', p)
                # Handle markdown-style italic
                p = re.sub(r'\*([^*]+)\*', r'<em>\1</em>', p)
                html_paragraphs.append(f"<p>{p}</p>")
        return "\n".join(html_paragraphs)

    def generate_pdf(
        self,
        result: MeetingResult,
        output_path: Path | None = None,
    ) -> Path:
        """
        Generate PDF meeting minutes.

        Args:
            result: The meeting result
            output_path: Output path (defaults to settings minutes_dir)

        Returns:
            Path to the generated PDF
        """
        if output_path is None:
            output_dir = self.settings.minutes_dir
            output_dir.mkdir(parents=True, exist_ok=True)
            output_path = output_dir / f"{result.meeting.month_str}.pdf"

        html_content = self.generate_html(result)
        css = CSS(string=FED_STYLE_CSS)

        HTML(string=html_content).write_pdf(
            output_path,
            stylesheets=[css],
        )

        return output_path

    def generate_all_formats(
        self,
        result: MeetingResult,
        output_dir: Path | None = None,
    ) -> dict[str, Path]:
        """
        Generate minutes in all formats (MD and PDF).

        Args:
            result: The meeting result
            output_dir: Output directory

        Returns:
            Dict mapping format to output path
        """
        if output_dir is None:
            output_dir = self.settings.minutes_dir
        output_dir.mkdir(parents=True, exist_ok=True)

        outputs = {}

        # Generate Markdown
        md_path = self.minutes_generator.save_markdown(result, output_dir)
        outputs["markdown"] = md_path

        # Generate PDF
        pdf_path = output_dir / f"{result.meeting.month_str}.pdf"
        self.generate_pdf(result, pdf_path)
        outputs["pdf"] = pdf_path

        return outputs
